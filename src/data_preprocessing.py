import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from config import (
    CATEGORICAL_FEATURES,
    DATASET_LABEL_TO_URGENCY_LEVEL,
    DATASET_PATH,
    FEATURE_COLUMNS,
    NO_COMORBIDITY_LABEL,
    NUMERIC_FEATURES,
    TARGET_COLUMN,
)


def load_clean_data():
    df = pd.read_csv(DATASET_PATH)

    df = df.drop_duplicates().reset_index(drop=True)

    df["comorbidities"] = df["comorbidities"].fillna(NO_COMORBIDITY_LABEL)

    for column in CATEGORICAL_FEATURES + [TARGET_COLUMN]:
        df[column] = df[column].str.strip()

    df[TARGET_COLUMN] = df[TARGET_COLUMN].map(DATASET_LABEL_TO_URGENCY_LEVEL)

    if df[TARGET_COLUMN].isnull().any():
        raise ValueError("Some urgency labels could not be mapped. Check DATASET_LABEL_TO_URGENCY_LEVEL in config.py.")
    if df[FEATURE_COLUMNS].isnull().any().any():
        raise ValueError("Missing values remain in the feature columns after cleaning.")

    return df[FEATURE_COLUMNS + [TARGET_COLUMN]]


def build_preprocessor():
    return ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), NUMERIC_FEATURES),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL_FEATURES,
            ),
        ]
    )


if __name__ == "__main__":
    raw_rows = len(pd.read_csv(DATASET_PATH))
    df = load_clean_data()

    print("=== Rows before and after removing duplicates ===")
    print(raw_rows, "->", len(df))

    print("\n=== First 5 cleaned rows ===")
    print(df.head())

    print("\n=== Class counts after cleaning ===")
    print(df[TARGET_COLUMN].value_counts())

    print("\n=== Comorbidities after filling missing values ===")
    print(df["comorbidities"].value_counts())

    preprocessor = build_preprocessor()
    encoded = preprocessor.fit_transform(df[FEATURE_COLUMNS])

    print("\n=== Demo only: shape after encoding and scaling ===")
    print(encoded.shape)

    print("\n=== Names of the model input columns ===")
    for name in preprocessor.get_feature_names_out():
        print(name)
