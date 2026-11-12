"""
Flask API so the PHP frontend (or M1's pipeline) can call the matching logic.

Run:     python api.py
Test:    curl -X POST http://127.0.0.1:5000/match -H "Content-Type: application/json" \
              -d '{"disease": "Chest Pain", "urgency": "Moderate"}'
Needs:   pip install flask
"""
from flask import Flask, jsonify, request
from scheduler import book_appointment, SPECIALTY_MAP, DOCTORS

app = Flask(__name__)


@app.post("/match")
def match():
    data = request.get_json(silent=True) or {}
    disease = data.get("disease")
    urgency = data.get("urgency")
    if not disease or not urgency:
        return jsonify({"error": "Both 'disease' and 'urgency' are required"}), 400
    try:
        return jsonify(book_appointment(disease, urgency))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.get("/doctors")
def doctors():
    return jsonify(DOCTORS)


@app.get("/diseases")
def diseases():
    return jsonify(sorted(SPECIALTY_MAP.keys()))


if __name__ == "__main__":
    app.run(debug=True, port=5000)