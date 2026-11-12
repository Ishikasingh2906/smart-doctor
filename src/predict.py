import joblib
import pandas as pd

from config import (
    CATEGORICAL_FEATURES,
    CODE_TO_URGENCY_LEVEL,
    FEATURE_COLUMNS,
    MAX_AGE,
    MIN_AGE,
    MODEL_PATH,
    NO_COMORBIDITY_LABEL,
    PREPROCESSOR_PATH,
    SYMPTOM_GROUPS,
)

DISCLAIMER = (
    "Academic prototype trained on a synthetic dataset. Not medical advice. "
    "In an emergency, contact your local emergency number immediately."
)


def _load_saved_file(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}. Run train.py and evaluate.py first.")
    return joblib.load(path)


_preprocessor = _load_saved_file(PREPROCESSOR_PATH)
_model = _load_saved_file(MODEL_PATH)


def get_input_options():
    encoder = _preprocessor.named_transformers_["categorical"]
    return {
        feature: [str(category) for category in categories]
        for feature, categories in zip(CATEGORICAL_FEATURES, encoder.categories_)
    }


def get_symptom_groups():
    return [
        {"symptom_1": first, "symptom_2": second, "symptom_3": third}
        for first, second, third in SYMPTOM_GROUPS
    ]


def _validate_patient_data(patient_data):
    if not isinstance(patient_data, dict):
        raise TypeError("patient_data must be a dictionary.")

    missing_fields = [field for field in FEATURE_COLUMNS if field not in patient_data]
    if missing_fields:
        raise ValueError(f"Missing required fields: {missing_fields}")

    age = patient_data["age"]
    if isinstance(age, bool) or not isinstance(age, (int, float)):
        raise ValueError("age must be a number.")
    if not MIN_AGE <= age <= MAX_AGE:
        raise ValueError(f"age must be between {MIN_AGE} and {MAX_AGE}.")

    options = get_input_options()
    cleaned = {"age": age}

    for feature in CATEGORICAL_FEATURES:
        value = patient_data[feature]
        if feature == "comorbidities" and (value is None or str(value).strip() == ""):
            value = NO_COMORBIDITY_LABEL
        if not isinstance(value, str):
            raise ValueError(f"{feature} must be text.")

        matches = {option.lower(): option for option in options[feature]}
        key = value.strip().lower()
        if key not in matches:
            raise ValueError(f"Invalid value '{value}' for {feature}. Allowed values: {options[feature]}")
        cleaned[feature] = matches[key]

    symptom_triple = (cleaned["symptom_1"], cleaned["symptom_2"], cleaned["symptom_3"])
    if symptom_triple not in SYMPTOM_GROUPS:
        raise ValueError(
            "This symptom combination is not one the model was trained on. "
            "Use one of the groups returned by get_symptom_groups()."
        )

    return cleaned


def predict_urgency(patient_data):
    cleaned = _validate_patient_data(patient_data)
    patient_frame = pd.DataFrame([cleaned], columns=FEATURE_COLUMNS)
    encoded = _preprocessor.transform(patient_frame)

    urgency_code = int(_model.predict(encoded)[0])
    result = {
        "urgency_level": CODE_TO_URGENCY_LEVEL[urgency_code],
        "urgency_code": urgency_code,
        "class_scores": None,
        "disclaimer": DISCLAIMER,
    }

    if hasattr(_model, "predict_proba"):
        scores = _model.predict_proba(encoded)[0]
        result["class_scores"] = {
            CODE_TO_URGENCY_LEVEL[int(code)]: round(float(score), 3)
            for code, score in zip(_model.classes_, scores)
        }

    return result


def predict_priority(patient_data):
    return predict_urgency(patient_data)["urgency_level"]