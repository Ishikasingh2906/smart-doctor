PRAGMA foreign_keys = ON;

-- Patients (patient login + basic details)
CREATE TABLE IF NOT EXISTS patients (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    age           INTEGER NOT NULL CHECK (age BETWEEN 0 AND 120),
    gender        TEXT NOT NULL,
    phone         TEXT,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Doctors (doctor login + profile)
CREATE TABLE IF NOT EXISTS doctors (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL,
    specialization TEXT NOT NULL,
    phone          TEXT,
    email          TEXT NOT NULL UNIQUE,
    password_hash  TEXT NOT NULL
);

-- Weekly availability template: one row = one working block on one weekday.
-- weekday: 0=Monday ... 6=Sunday (same as Python's date.weekday()).
-- Concrete slots are generated from this, so we never store thousands of empty slots.
CREATE TABLE IF NOT EXISTS doctor_availability (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id    INTEGER NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    weekday      INTEGER NOT NULL CHECK (weekday BETWEEN 0 AND 6),
    start_time   TEXT NOT NULL,          -- 'HH:MM'
    end_time     TEXT NOT NULL,          -- 'HH:MM'
    slot_minutes INTEGER NOT NULL DEFAULT 20
);

-- Booked slots
CREATE TABLE IF NOT EXISTS appointments (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    doctor_id  INTEGER NOT NULL REFERENCES doctors(id),
    appt_date  TEXT NOT NULL,            -- 'YYYY-MM-DD'
    appt_time  TEXT NOT NULL,            -- 'HH:MM'
    urgency    TEXT NOT NULL CHECK (urgency IN ('Very Urgent','Moderate','Not Urgent')),
    status     TEXT NOT NULL DEFAULT 'Booked' CHECK (status IN ('Booked','Cancelled','Completed')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- THE double-booking guard: the database itself refuses a second active booking
-- for the same doctor/date/time (cancelled rows don't block the slot).
CREATE UNIQUE INDEX IF NOT EXISTS ux_active_slot
    ON appointments(doctor_id, appt_date, appt_time) WHERE status = 'Booked';

CREATE INDEX IF NOT EXISTS ix_appt_patient ON appointments(patient_id);
CREATE INDEX IF NOT EXISTS ix_appt_doctor_date ON appointments(doctor_id, appt_date);

-- MCQ answers + what the model predicted (useful for the doctor view and for retraining later)
CREATE TABLE IF NOT EXISTS patient_responses (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id        INTEGER NOT NULL REFERENCES patients(id),
    appointment_id    INTEGER REFERENCES appointments(id),
    answers_json      TEXT NOT NULL,
    predicted_urgency TEXT NOT NULL,
    ml_urgency        TEXT,              -- what the ML model said before any safety override
    emergency_flag    INTEGER NOT NULL DEFAULT 0,
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);
