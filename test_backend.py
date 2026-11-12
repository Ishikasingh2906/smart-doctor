"""End-to-end backend tests. Run:  python test_backend.py"""
import os
import sqlite3
import tempfile
from datetime import datetime

from app import create_app
import db as dbm

NOW = datetime(2026, 11, 9, 22, 35)      # Monday night -> urgent patients must roll to tomorrow
DB = os.path.join(tempfile.mkdtemp(), "test.db")
app = create_app(DB, now_func=lambda: NOW)

BASE = {"problem_area": "Heart / chest", "severity": "Mild", "duration": "1-3 days", "fever": "No",
        "breathing": "No", "chest_pain": "No", "bleeding": "No", "worsening": "No"}


def patient(client, email):
    r = client.post("/api/patient/register", json={"name": "Test " + email, "age": 30, "gender": "Male",
                                                  "email": email, "password": "secret1"})
    assert r.status_code == 201, r.json
    return r.json["patient_id"]


def book(client, **over):
    return client.post("/api/patient/book", json={"answers": {**BASE, **over}})


def run():
    c = app.test_client()
    print("seed:", len(c.get("/api/doctors").json), "doctors")
    assert len(c.get("/api/doctors").json) == 10

    # --- auth rules
    assert book(c).status_code == 401
    patient(c, "a@x.com")
    assert c.post("/api/patient/register", json={"name": "d", "age": 3, "gender": "M", "email": "a@x.com",
                                                 "password": "secret1"}).status_code == 409
    c.post("/api/logout")
    assert c.post("/api/patient/login", json={"email": "a@x.com", "password": "bad"}).status_code == 401
    assert c.post("/api/patient/login", json={"email": "a@x.com", "password": "secret1"}).status_code == 200

    # --- validation
    assert c.post("/api/patient/book", json={"answers": {"problem_area": "Skin"}}).status_code == 400
    assert book(c, severity="Banana").status_code == 400

    # --- the three urgency windows (now = Mon 22:35)
    r = book(c, severity="Severe", fever="High", worsening="Quickly", duration="Less than 1 day").json
    print("Very Urgent  ->", r["appointment"]["doctor_name"], r["appointment"]["day"], r["appointment"]["date"], r["appointment"]["time"])
    assert r["urgency"] == "Very Urgent" and r["appointment"]["date"] == "2026-11-10"      # tomorrow
    assert r["appointment"]["specialization"] == "Cardiologist"

    r = book(c, severity="Moderate", fever="Mild", duration="4-7 days", worsening="Slowly").json
    print("Moderate     ->", r["appointment"]["doctor_name"], r["appointment"]["day"], r["appointment"]["date"], r["appointment"]["time"])
    assert r["urgency"] == "Moderate" and r["appointment"]["date"] >= "2026-11-10"

    r = book(c).json
    print("Not Urgent   ->", r["appointment"]["doctor_name"], r["appointment"]["day"], r["appointment"]["date"], r["appointment"]["time"])
    assert r["urgency"] == "Not Urgent" and r["appointment"]["date"] >= "2026-11-11"       # day after tomorrow+

    # --- red flag override: ML-style "mild" answers but severe chest pain => Very Urgent + warning
    r = book(c, chest_pain="Severe").json
    print("Red flag     ->", r["urgency"], "| warning:", bool(r["emergency_warning"]))
    assert r["urgency"] == "Very Urgent" and r["emergency_warning"] and r["emergency_message"]

    # --- different specialties route correctly
    r = book(c, problem_area="Skin").json
    assert r["appointment"]["specialization"] == "Dermatologist"

    # --- DB-level double-booking guard
    conn = sqlite3.connect(DB)
    row = conn.execute("SELECT patient_id, doctor_id, appt_date, appt_time FROM appointments LIMIT 1").fetchone()
    try:
        conn.execute("INSERT INTO appointments (patient_id, doctor_id, appt_date, appt_time, urgency) "
                     "VALUES (?,?,?,?, 'Moderate')", row)
        raise SystemExit("FAIL: double booking was allowed")
    except sqlite3.IntegrityError:
        print("DB rejected a double booking (unique index works)")
    conn.close()

    # --- many patients, same doctor: every slot unique
    for i in range(12):
        c.post("/api/logout"); patient(c, f"p{i}@x.com"); assert book(c).status_code == 201
    conn = sqlite3.connect(DB)
    dup = conn.execute("SELECT COUNT(*) FROM (SELECT 1 FROM appointments WHERE status='Booked' "
                       "GROUP BY doctor_id, appt_date, appt_time HAVING COUNT(*)>1)").fetchone()[0]
    assert dup == 0
    conn.close()
    print("19 bookings, 0 duplicate slots")

    # --- fallback: fill every Cardiologist slot for tomorrow+today, Very Urgent must go to a General Physician
    conn = dbm.connect(DB)
    from scheduler import free_slots
    from datetime import date
    cardio = conn.execute("SELECT id FROM doctors WHERE specialization='Cardiologist'").fetchone()["id"]
    pid = conn.execute("SELECT id FROM patients LIMIT 1").fetchone()["id"]
    for s in free_slots(conn, cardio, NOW, date(2026, 11, 10)):
        conn.execute("INSERT INTO appointments (patient_id, doctor_id, appt_date, appt_time, urgency) VALUES (?,?,?,?,?)",
                     (pid, cardio, s.date().isoformat(), s.strftime("%H:%M"), "Moderate"))
    conn.commit(); conn.close()
    r = book(c, chest_pain="Severe").json
    print("Fallback     ->", r["appointment"]["specialization"], "|", r["appointment"]["note"][:60], "...")
    assert r["appointment"]["specialization"] == "General Physician" and r["appointment"]["note"]

    # --- patient sees own appointments, can cancel, slot is freed
    mine = c.get("/api/patient/appointments").json
    assert len(mine) >= 1
    aid = mine[0]["id"]
    assert c.post(f"/api/patient/appointments/{aid}/cancel").status_code == 200
    assert c.post(f"/api/patient/appointments/{aid}/cancel").status_code == 404

    # --- doctor side
    c.post("/api/logout")
    assert c.get("/api/doctor/appointments").status_code == 401
    assert c.post("/api/doctor/login", json={"email": "doctor1@hospital.com", "password": "nope"}).status_code == 401
    d = c.post("/api/doctor/login", json={"email": "doctor1@hospital.com", "password": "doctor123"}).json
    print("Doctor login ->", d["name"], "/", d["specialization"])
    appts = c.get("/api/doctor/appointments").json
    assert appts and all("patient_name" in a and "urgency" in a and "answers" in a for a in appts)
    print("Doctor sees", len(appts), "appointments; first:", appts[0]["patient_name"], appts[0]["appt_date"], appts[0]["appt_time"], appts[0]["urgency"])
    av = c.get("/api/doctor/availability").json
    assert av["weekly_schedule"] and av["free_slots"] is not None
    assert c.post(f"/api/doctor/appointments/{appts[0]['id']}/complete").status_code == 200
    # a patient token must not open the doctor dashboard
    c.post("/api/logout"); patient(c, "zz@x.com")
    assert c.get("/api/doctor/appointments").status_code == 401

    print("\nALL BACKEND TESTS PASSED")


if __name__ == "__main__":
    run()