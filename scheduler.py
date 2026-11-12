"""
Database-backed scheduling (replaces the in-memory scheduler from the first version).

Urgency rules (prototype):
  Very Urgent : today (>= 15 min from now) or tomorrow
  Moderate    : tomorrow or later (searches up to 7 days ahead)
  Not Urgent  : from day-after-tomorrow onwards (searches up to 14 days ahead)

If no slot exists for the right specialist:
  1. Very Urgent -> try a General Physician inside the same today/tomorrow window
  2. otherwise   -> widen the search to ANY doctor, up to 7 days, and flag it with a note
  3. still nothing -> returns None (the API tells the patient to contact the hospital desk)
"""
import sqlite3
from datetime import datetime, timedelta, date, time

URGENT_LEAD_MINUTES = 15
GENERAL = "General Physician"

# (first_day_offset, last_day_offset) counted from today
WINDOWS = {
    "Very Urgent": (0, 1),
    "Moderate":    (1, 7),
    "Not Urgent":  (2, 14),
}


def _hm(s):
    h, m = map(int, s.split(":"))
    return time(h, m)


def free_slots(conn, doctor_id, earliest: datetime, last_day: date):
    """All free slot datetimes for one doctor from `earliest` up to the end of `last_day`, in order."""
    blocks = conn.execute(
        "SELECT weekday, start_time, end_time, slot_minutes FROM doctor_availability WHERE doctor_id=?",
        (doctor_id,)).fetchall()
    booked = {
        (r["appt_date"], r["appt_time"]) for r in conn.execute(
            "SELECT appt_date, appt_time FROM appointments WHERE doctor_id=? AND status='Booked' "
            "AND appt_date BETWEEN ? AND ?",
            (doctor_id, earliest.date().isoformat(), last_day.isoformat()))
    }
    out = []
    day = earliest.date()
    while day <= last_day:
        for b in blocks:
            if b["weekday"] != day.weekday():
                continue
            t = datetime.combine(day, _hm(b["start_time"]))
            end = datetime.combine(day, _hm(b["end_time"]))
            step = timedelta(minutes=b["slot_minutes"])
            while t + step <= end:
                if t >= earliest and (day.isoformat(), t.strftime("%H:%M")) not in booked:
                    out.append(t)
                t += step
        day += timedelta(days=1)
    return sorted(out)


def _window(urgency, now):
    first, last = WINDOWS[urgency]
    if urgency == "Very Urgent":
        earliest = now + timedelta(minutes=URGENT_LEAD_MINUTES)
    else:
        earliest = datetime.combine(now.date() + timedelta(days=first), time(0, 0))
    return earliest, now.date() + timedelta(days=last)


def _best(conn, doctors, earliest, last_day):
    best = None
    for d in doctors:
        slots = free_slots(conn, d["id"], earliest, last_day)
        if slots and (best is None or slots[0] < best[1]):
            best = (d, slots[0])
    return best


def find_slot(conn, specialization, urgency, now):
    """Return (doctor_row, slot_datetime, note) or None."""
    earliest, last_day = _window(urgency, now)
    doctors = conn.execute("SELECT * FROM doctors WHERE specialization=?", (specialization,)).fetchall()
    hit = _best(conn, doctors, earliest, last_day)
    if hit:
        return hit[0], hit[1], ""

    if urgency == "Very Urgent" and specialization != GENERAL:
        gps = conn.execute("SELECT * FROM doctors WHERE specialization=?", (GENERAL,)).fetchall()
        hit = _best(conn, gps, earliest, last_day)
        if hit:
            return hit[0], hit[1], (f"No {specialization} slot free today/tomorrow, so you were booked with "
                                    f"a General Physician who can assess you and refer you on.")

    everyone = conn.execute("SELECT * FROM doctors").fetchall()
    hit = _best(conn, everyone, earliest, now.date() + timedelta(days=7))
    if hit:
        return hit[0], hit[1], (f"No {specialization} slot available in the normal window; "
                                f"booked the earliest available doctor instead.")
    return None


def book(conn, patient_id, specialization, urgency, now=None):
    """Find a slot and insert the appointment. Retries if another patient grabs the slot first.
    Returns a dict (appointment + doctor + note) or None when nothing is available."""
    now = now or datetime.now()
    for _ in range(5):
        found = find_slot(conn, specialization, urgency, now)
        if not found:
            return None
        doctor, slot, note = found
        try:
            cur = conn.execute(
                "INSERT INTO appointments (patient_id, doctor_id, appt_date, appt_time, urgency) VALUES (?,?,?,?,?)",
                (patient_id, doctor["id"], slot.date().isoformat(), slot.strftime("%H:%M"), urgency))
        except sqlite3.IntegrityError:
            continue  # slot was taken a moment ago -> search again
        return {
            "appointment_id": cur.lastrowid,
            "doctor_id": doctor["id"],
            "doctor_name": doctor["name"],
            "specialization": doctor["specialization"],
            "date": slot.date().isoformat(),
            "day": slot.strftime("%A"),
            "time": slot.strftime("%H:%M"),
            "urgency": urgency,
            "note": note  ,
        }
    return None