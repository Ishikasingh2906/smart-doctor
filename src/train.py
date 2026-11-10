import joblib
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from config import (
    FEATURE_COLUMNS,
    MODELS_DIR,
    PREPROCESSOR_PATH,
    RANDOM_STATE,
    TARGET_COLUMN,
    TEST_SIZE,
    URGENCY_LEVEL_TO_CODE,
)
from data_preprocessing import build_preprocessor, load_clean_data

CANDIDATE_MODELS_DIR = MODELS_DIR / "candidates"


def get_train_test_split():
    df = load_clean_data()
    features = df[FEATURE_COLUMNS]
    target = df[TARGET_COLUMN].map(URGENCY_LEVEL_TO_CODE)

    return train_test_split(
        features,
        target,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=target,
    )


def get_candidate_models():
    return {
        "Baseline (most frequent)": DummyClassifier(strategy="most_frequent"),
        "Logistic Regression": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "Decision Tree": DecisionTreeClassifier(
            max_depth=5, class_weight="balanced", random_state=RANDOM_STATE
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=200,
            max_depth=8,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        ),
        "K-Nearest Neighbours": KNeighborsClassifier(n_neighbors=15),
        "Support Vector Machine": SVC(class_weight="balanced", random_state=RANDOM_STATE),
    }


def model_file_name(model_name):
    cleaned = model_name.lower().replace(" ", "_").replace("(", "").replace(")", "")
    return cleaned + ".joblib"


if __name__ == "__main__":
    X_train, X_test, y_train, y_test = get_train_test_split()

    print("=== Split sizes ===")
    print("Training rows:", len(X_train))
    print("Testing rows: ", len(X_test))

    print("\n=== Class share (%) in training and testing data ===")
    print("Training:", (y_train.value_counts(normalize=True).sort_index() * 100).round(1).to_dict())
    print("Testing: ", (y_test.value_counts(normalize=True).sort_index() * 100).round(1).to_dict())

    preprocessor = build_preprocessor()
    X_train_encoded = preprocessor.fit_transform(X_train)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    CANDIDATE_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(preprocessor, PREPROCESSOR_PATH)
    print("\nSaved preprocessing pipeline to:", PREPROCESSOR_PATH)

    print("\n=== Training models ===")
    for model_name, model in get_candidate_models().items():
        model.fit(X_train_encoded, y_train)
        training_accuracy = model.score(X_train_encoded, y_train)
        joblib.dump(model, CANDIDATE_MODELS_DIR / model_file_name(model_name))
        print(f"{model_name:<28} training accuracy: {training_accuracy:.3f}")

    print("\nAll candidate models saved in:", CANDIDATE_MODELS_DIR)