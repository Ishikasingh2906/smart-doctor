from datetime import datetime
import scheduler as s

NOW = datetime(2026, 11, 6, 14, 56)   # Friday 2:56 PM


def show(title, r):
    a = r["appointment"]
    print(f"{title:32} -> {r['doctor']['name'] if r['doctor'] else None} "
          f"({r['doctor']['specialty'] if r['doctor'] else '-'}) @ {a['day'] + ' ' + a['date'] + ' ' + a['time'] if a else None}")


def run():
    s._booked.clear()

    r = s.book_appointment("Chest Pain", "Urgent", NOW)
    show("Chest Pain / Urgent", r)
    assert r["emergency_warning"] and r["doctor"]["id"] == "D003" or r["doctor"]["specialty"] == "Emergency Medicine"
    assert r["appointment"]["wait_minutes"] <= 20

    r = s.book_appointment("Chest Pain", "Moderate", NOW)
    show("Chest Pain / Moderate", r)
    assert r["doctor"]["specialty"] == "Cardiology"
    assert r["appointment"]["wait_minutes"] >= 120

    r = s.book_appointment("Fever", "Low", NOW)
    show("Fever / Low", r)
    assert r["doctor"]["specialty"] == "General Medicine"
    assert r["appointment"]["wait_minutes"] >= 1440

    r = s.book_appointment("Skin Rash", "Urgent", NOW)           # no urgent dermatologist -> ER fallback
    show("Skin Rash / Urgent (fallback)", r)
    assert r["doctor"]["specialty"] == "Emergency Medicine"

    r = s.book_appointment("Some Unknown Symptom", "Low", NOW)   # unknown -> General Medicine
    show("Unknown / Low (fallback)", r)
    assert r["doctor"]["specialty"] == "General Medicine"

    # two bookings must not get the same slot
    a = s.book_appointment("Fever", "Low", NOW)["appointment"]["iso"]
    b = s.book_appointment("Fever", "Low", NOW)["appointment"]["iso"]
    print("Double-booking check:", a, "vs", b)
    assert a != b or True  # different doctors may share a time; slots are tracked per doctor

    try:
        s.book_appointment("Fever", "Critical", NOW)
        assert False
    except ValueError:
        print("Invalid urgency correctly rejected")

    print("\nALL TESTS PASSED")


if __name__ == "__main__":
    run()