"""Fill the database with the 10 prototype doctors and their weekly availability.

Run:  python seed.py
Doctor logins:  doctor1@hospital.com ... doctor10@hospital.com   password: doctor123
(change DOCTOR_PASSWORD before any real use)
"""
from werkzeug.security import generate_password_hash

from db import connect, init_db

DOCTOR_PASSWORD = "doctor123"

# (name, specialization, phone, [(weekday, start, end, slot_minutes), ...])   weekday: 0=Mon
Mon_Fri = [0, 1, 2, 3, 4]
DOCTORS = [
    ("Dr. Meera Iyer",      "Cardiologist",         "9000000001", [(d, "09:00", "13:00", 20) for d in Mon_Fri]),
    ("Dr. Vikram Singh",    "Orthopaedic",          "9000000002", [(d, "10:00", "16:00", 20) for d in [0, 1, 2, 3, 4, 5]]),
    ("Dr. Arjun Nair",      "Neurologist",          "9000000003", [(d, "10:00", "15:00", 30) for d in [0, 2, 4]]),
    ("Dr. Neha Kapoor",     "Dermatologist",        "9000000004", [(d, "11:00", "17:00", 15) for d in [0, 1, 2, 3, 4, 5]]),
    ("Dr. Anita Sharma",    "General Physician",    "9000000005", [(d, "09:00", "13:00", 15) for d in range(6)] +
                                                                  [(d, "14:00", "17:00", 15) for d in range(6)]),
    ("Dr. Pooja Gupta",     "Gastroenterologist",   "9000000006", [(d, "09:00", "14:00", 20) for d in Mon_Fri]),
    ("Dr. Rohan Desai",     "Ophthalmologist",      "9000000007", [(d, "10:00", "16:00", 20) for d in [1, 2, 3, 4, 5]]),
    ("Dr. Farah Khan",      "ENT Specialist",       "9000000008", [(d, "10:00", "16:00", 15) for d in Mon_Fri]),
    ("Dr. Sunita Rao",      "Pulmonologist",        "9000000009", [(d, "09:30", "15:30", 20) for d in Mon_Fri]),
    ("Dr. Karan Malhotra",  "Physiotherapist",      "9000000010", [(d, "08:00", "14:00", 30) for d in [0, 1, 2, 3, 4, 5]]),
]


def seed(db_path=None):
    init_db(db_path)
    conn = connect(db_path)
    if conn.execute("SELECT COUNT(*) FROM doctors").fetchone()[0]:
        conn.close()
        return False  # already seeded
    pw = generate_password_hash(DOCTOR_PASSWORD)
    for i, (name, spec, phone, blocks) in enumerate(DOCTORS, start=1):
        cur = conn.execute(
            "INSERT INTO doctors (name, specialization, phone, email, password_hash) VALUES (?,?,?,?,?)",
            (name, spec, phone, f"doctor{i}@hospital.com", pw))
        conn.executemany(
            "INSERT INTO doctor_availability (doctor_id, weekday, start_time, end_time, slot_minutes) "
            "VALUES (?,?,?,?,?)",
            [(cur.lastrowid, *b) for b in blocks])
    conn.commit()
    conn.close()
    return True


if __name__ == "__main__":
    print("Seeded 10 doctors." if seed() else "Database already has doctors - nothing to do.")