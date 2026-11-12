"""
Bridge between the backend and Member A's trained model.

CONTRACT with Member A (ML):
    Save the final sklearn pipeline as  model.joblib  in this folder. It must accept a
    pandas DataFrame with ONE row whose columns are the question ids in questions.json
    (raw text answers, e.g. "Severe") - i.e. the pipeline should include its own encoder -
    and predict one of: "Very Urgent", "Moderate", "Not Urgent".

Until model.joblib exists, a simple rule-based fallback keeps the whole app working
so you (and the frontend) can test end-to-end.
"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
MODEL_PATH = BASE_DIR / "model.joblib"
LABELS = ("Very Urgent", "Moderate", "Not Urgent")

_model = None
_model_loaded = False


def _load_model():
    global _model, _model_loaded
    if not _model_loaded:
        _model_loaded = True
        if MODEL_PATH.exists():
            import joblib
            _model = joblib.load(MODEL_PATH)
    return _model


def _fallback_rules(a):
    """Crude scoring so the prototype works before the real model is ready."""
    pts = {"Mild": 1, "Slight": 1, "Moderate": 2, "Severe": 4, "High": 3, "Yes": 4, "Quickly": 3, "Slowly": 1}
    score = sum(pts.get(a.get(k), 0) for k in ("severity", "fever", "breathing", "chest_pain", "bleeding", "worsening"))
    if a.get("duration") == "Less than 1 day":
        score += 1
    if score >= 8:
        return "Very Urgent"
    if score >= 4:
        return "Moderate"
    return "Not Urgent"


def predict_urgency(answers: dict) -> str:
    """answers: {question_id: chosen option text} -> 'Very Urgent' | 'Moderate' | 'Not Urgent'"""
    model = _load_model()
    if model is None:
        return _fallback_rules(answers)
    import pandas as pd
    label = str(model.predict(pd.DataFrame([answers]))[0])
    if label not in LABELS:
        raise ValueError(f"Model returned unexpected label {label!r}; expected one of {LABELS}")
    return label


def using_real_model() -> bool:
    return _load_model() is not None