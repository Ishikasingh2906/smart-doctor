from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_PATH = PROJECT_ROOT / "dataset" / "medical_symptom_triage.csv"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
MODEL_PATH = MODELS_DIR / "trained_model.joblib"
PREPROCESSOR_PATH = MODELS_DIR / "preprocessing_pipeline.joblib"

TARGET_COLUMN = "urgency"
NUMERIC_FEATURES = ["age"]
CATEGORICAL_FEATURES = ["gender", "comorbidities", "symptom_1", "symptom_2", "symptom_3"]
FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES

NO_COMORBIDITY_LABEL = "None"

DATASET_LABEL_TO_URGENCY_LEVEL = {
    "Low": "Not Urgent",
    "Medium": "Moderate",
    "High": "Very Urgent",
}
URGENCY_LEVEL_TO_CODE = {
    "Not Urgent": 0,
    "Moderate": 1,
    "Very Urgent": 2,
}
CODE_TO_URGENCY_LEVEL = {code: level for level, code in URGENCY_LEVEL_TO_CODE.items()}

TEST_SIZE = 0.2
RANDOM_STATE = 42
