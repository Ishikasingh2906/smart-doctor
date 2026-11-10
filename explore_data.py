import pandas as pd

from config import DATASET_PATH, TARGET_COLUMN

df = pd.read_csv(DATASET_PATH)

print("=== Shape (rows, columns) ===")
print(df.shape)

print("\n=== First 5 rows ===")
print(df.head())

print("\n=== Column types ===")
print(df.dtypes)

print("\n=== Missing values per column ===")
print(df.isnull().sum())

print("\n=== Number of duplicate rows ===")
print(df.duplicated().sum())

print("\n=== Target column: class counts ===")
print(df[TARGET_COLUMN].value_counts())

print("\n=== Comorbidities (including missing) ===")
print(df["comorbidities"].value_counts(dropna=False))

print("\n=== Unique values per column ===")
print(df.nunique())

print("\n=== Age summary ===")
print(df["age"].describe())