"""
Flask backend: auth (patient + doctor), questionnaire, ML prediction, booking, dashboards.

Run:  python seed.py && python app.py        -> http://127.0.0.1:5000
"""
import json
import os
import re
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import Flask, g, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

import db as dbm
import ml_interface
import scheduler
from seed import seed

BASE_DIR = Path(__file__).parent
CONFIG = json.loads((BASE_DIR / "questions.json").read_text(encoding="utf-8"))
QUESTIONS = CONFIG["questions"]
SPECIALIZATION_MAP = CONFIG["problem_area_to_specialization"]
RED_FLAGS = CONFIG["red_flags"]
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def create_app(db_path=None, now_func=datetime.now):
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")
    app.config["DB_PATH"] = db_path or dbm.DEFAULT_DB
    app.config["NOW"] = now_func
    seed(app.config["DB_PATH"])          # creates tables + 10 doctors on first run

    @app.before_request
    def _open_db():
        g.db_path = app.config["DB_PATH"]

    app.teardown_appcontext(dbm.close_db)

    # ---------- helpers ----------
    def err(msg, code=400):
        return jsonify({"error": msg}), code

    def login_required(role):
        def deco(fn):
            @wraps(fn)
            def wrapper(*a, **kw):
                if session.get("role") != role:
                    return err(f"{role} login required", 401)
                return fn(*a, **kw)
            return wrapper
        return deco

    def emergency_flag(answers):
        return any(answers.get(r["question"]) == r["answer"] for r in RED_FLAGS)

    # ---------- public ----------
    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "real_ml_model": ml_interface.using_real_model()})

    @app.get("/api/questions")
    def questions():
        return jsonify(QUESTIONS)

    @app.get("/api/doctors")
    def doctors():
        rows = dbm.get_db().execute("SELECT id, name, specialization, phone FROM doctors").fetchall()
        return jsonify([dict(r) for r in rows])

    @app.post("/api/logout")
    def logout():
        session.clear()
        return jsonify({"ok": True})

    # ---------- patient auth ----------
    @app.post("/api/patient/register")
    def patient_register():
        d = request.get_json(silent=True) or {}
        name, email, pw = (d.get("name") or "").strip(), (d.get("email") or "").strip().lower(), d.get("password") or ""
        gender, phone = d.get("gender"), d.get("phone")
        try:
            age = int(d.get("age"))
        except (TypeError, ValueError):
            return err("age must be a number")
        if not name or not gender:
            return err("name and gender are required")
        if not EMAIL_RE.match(email):
            return err("valid email required")
        if len(pw) < 6:
            return err("password must be at least 6 characters")
        if not 0 <= age <= 120:
            return err("age must be between 0 and 120")
        conn = dbm.get_db()
        try:
            cur = conn.execute(
                "INSERT INTO patients (name, age, gender, phone, email, password_hash) VALUES (?,?,?,?,?,?)",
                (name, age, gender, phone, email, generate_password_hash(pw)))
            conn.commit()
        except Exception:
            return err("this email is already registered", 409)
        session.clear()
        session.update(role="patient", uid=cur.lastrowid)
        return jsonify({"patient_id": cur.lastrowid, "name": name}), 201

    @app.post("/api/patient/login")
    def patient_login():
        d = request.get_json(silent=True) or {}
        row = dbm.get_db().execute("SELECT * FROM patients WHERE email=?",
                                   ((d.get("email") or "").strip().lower(),)).fetchone()
        if not row or not check_password_hash(row["password_hash"], d.get("password") or ""):
            return err("invalid email or password", 401)
        session.clear()
        session.update(role="patient", uid=row["id"])
        return jsonify({"patient_id": row["id"], "name": row["name"]})

    # ---------- patient: predict + book ----------
    @app.post("/api/patient/book")
    @login_required("patient")
    def patient_book():
        answers = (request.get_json(silent=True) or {}).get("answers")
        if not isinstance(answers, dict):
            return err("send {'answers': {question_id: option}}")
        missing = [q["id"] for q in QUESTIONS if q["id"] not in answers]
        if missing:
            return err(f"missing answers: {', '.join(missing)}")
        bad = [q["id"] for q in QUESTIONS if answers[q["id"]] not in q["options"]]
        if bad:
            return err(f"invalid option for: {', '.join(bad)}")

        specialization = SPECIALIZATION_MAP[answers["problem_area"]]
        ml_label = ml_interface.predict_urgency(answers)
        emergency = emergency_flag(answers)
        urgency = "Very Urgent" if emergency else ml_label   # safety override: red flags always top priority

        conn = dbm.get_db()
        try:
            conn.execute("BEGIN IMMEDIATE")      # take the write lock so two bookings can't race
            booking = scheduler.book(conn, session["uid"], specialization, urgency, app.config["NOW"]())
            conn.execute(
                "INSERT INTO patient_responses (patient_id, appointment_id, answers_json, predicted_urgency, "
                "ml_urgency, emergency_flag) VALUES (?,?,?,?,?,?)",
                (session["uid"], booking["appointment_id"] if booking else None,
                 json.dumps(answers), urgency, ml_label, int(emergency)))
            conn.commit()
        except Exception:
            conn.rollback()
            raise

        resp = {"urgency": urgency, "specialization": specialization, "emergency_warning": emergency,
                "emergency_message": ("Your answers include warning signs. Please go to the nearest emergency "
                                      "room or call emergency services now - do not wait for this appointment.")
                if emergency else None,
                "appointment": booking}
        if not booking:
            resp["message"] = "No slot is currently available. Please contact the hospital desk."
        return jsonify(resp), 201 if booking else 200

    @app.get("/api/patient/appointments")
    @login_required("patient")
    def patient_appointments():
        rows = dbm.get_db().execute(
            "SELECT a.id, a.appt_date, a.appt_time, a.urgency, a.status, d.name AS doctor_name, "
            "d.specialization FROM appointments a JOIN doctors d ON d.id=a.doctor_id "
            "WHERE a.patient_id=? ORDER BY a.appt_date, a.appt_time", (session["uid"],)).fetchall()
        return jsonify([dict(r) for r in rows])

    @app.post("/api/patient/appointments/<int:appt_id>/cancel")
    @login_required("patient")
    def patient_cancel(appt_id):
        conn = dbm.get_db()
        cur = conn.execute("UPDATE appointments SET status='Cancelled' WHERE id=? AND patient_id=? "
                           "AND status='Booked'", (appt_id, session["uid"]))
        conn.commit()
        if cur.rowcount == 0:
            return err("appointment not found or already closed", 404)
        return jsonify({"ok": True})

    # ---------- doctor ----------
    @app.post("/api/doctor/login")
    def doctor_login():
        d = request.get_json(silent=True) or {}
        row = dbm.get_db().execute("SELECT * FROM doctors WHERE email=?",
                                   ((d.get("email") or "").strip().lower(),)).fetchone()
        if not row or not check_password_hash(row["password_hash"], d.get("password") or ""):
            return err("invalid email or password", 401)
        session.clear()
        session.update(role="doctor", uid=row["id"])
        return jsonify({"doctor_id": row["id"], "name": row["name"], "specialization": row["specialization"]})

    @app.get("/api/doctor/appointments")
    @login_required("doctor")
    def doctor_appointments():
        """Optional ?date=YYYY-MM-DD. Default: today onwards. Sorted by date, time; urgent first within a day."""
        date = request.args.get("date")
        sql = ("SELECT a.id, a.appt_date, a.appt_time, a.urgency, a.status, p.name AS patient_name, p.age, "
               "p.gender, p.phone, r.answers_json FROM appointments a JOIN patients p ON p.id=a.patient_id "
               "LEFT JOIN patient_responses r ON r.appointment_id=a.id "
               "WHERE a.doctor_id=? AND a.status='Booked' ")
        args = [session["uid"]]
        if date:
            sql += "AND a.appt_date=? "
            args.append(date)
        else:
            sql += "AND a.appt_date>=? "
            args.append(app.config["NOW"]().date().isoformat())
        sql += "ORDER BY a.appt_date, a.appt_time"
        out = []
        for r in dbm.get_db().execute(sql, args).fetchall():
            row = dict(r)
            row["answers"] = json.loads(row.pop("answers_json")) if row["answers_json"] else None
            out.append(row)
        return jsonify(out)

    @app.get("/api/doctor/availability")
    @login_required("doctor")
    def doctor_availability():
        """Weekly template + free/booked slots for the next 7 days."""
        conn = dbm.get_db()
        now = app.config["NOW"]()
        from datetime import timedelta
        last = now.date() + timedelta(days=6)
        free = scheduler.free_slots(conn, session["uid"], datetime.combine(now.date(), datetime.min.time()), last)
        booked = conn.execute(
            "SELECT appt_date, appt_time, urgency FROM appointments WHERE doctor_id=? AND status='Booked' "
            "AND appt_date BETWEEN ? AND ? ORDER BY appt_date, appt_time",
            (session["uid"], now.date().isoformat(), last.isoformat())).fetchall()
        weekly = conn.execute("SELECT weekday, start_time, end_time, slot_minutes FROM doctor_availability "
                              "WHERE doctor_id=? ORDER BY weekday, start_time", (session["uid"],)).fetchall()
        return jsonify({"weekly_schedule": [dict(r) for r in weekly],
                        "free_slots": [s.strftime("%Y-%m-%d %H:%M") for s in free],
                        "booked_slots": [dict(r) for r in booked]})

    @app.post("/api/doctor/appointments/<int:appt_id>/complete")
    @login_required("doctor")
    def doctor_complete(appt_id):
        conn = dbm.get_db()
        cur = conn.execute("UPDATE appointments SET status='Completed' WHERE id=? AND doctor_id=? "
                           "AND status='Booked'", (appt_id, session["uid"]))
        conn.commit()
        if cur.rowcount == 0:
            return err("appointment not found", 404)
        return jsonify({"ok": True})

    return app


# Expose global app instance for Gunicorn
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)