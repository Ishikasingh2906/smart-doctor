import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from config import REPORTS_DIR, TARGET_COLUMN, URGENCY_LEVEL_TO_CODE
from data_preprocessing import load_clean_data

URGENCY_ORDER = list(URGENCY_LEVEL_TO_CODE.keys())
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)

FIGURES_DIR = REPORTS_DIR / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

df = load_clean_data()
df["symptom_group"] = df["symptom_1"] + " + " + df["symptom_2"] + " + " + df["symptom_3"]


def save_figure(file_name):
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / file_name, dpi=120)
    plt.close()
    print("Saved:", FIGURES_DIR / file_name)


plt.figure(figsize=(6, 4))
sns.countplot(data=df, x=TARGET_COLUMN, order=URGENCY_ORDER)
plt.title("Number of patients in each urgency class")
save_figure("1_class_distribution.png")

plt.figure(figsize=(7, 4))
sns.boxplot(data=df, x=TARGET_COLUMN, y="age", order=URGENCY_ORDER)
plt.title("Age of patients in each urgency class")
save_figure("2_age_by_urgency.png")

plt.figure(figsize=(7, 4))
comorbidity_share = (
    df.groupby("comorbidities")[TARGET_COLUMN].value_counts(normalize=True).unstack(fill_value=0)[URGENCY_ORDER] * 100
)
sns.heatmap(comorbidity_share, annot=True, fmt=".0f", cmap="Blues")
plt.title("% of each comorbidity group in each urgency class")
save_figure("3_comorbidities_by_urgency.png")

plt.figure(figsize=(10, 6))
symptom_share = (
    df.groupby("symptom_group")[TARGET_COLUMN].value_counts(normalize=True).unstack(fill_value=0)[URGENCY_ORDER] * 100
)
sns.heatmap(symptom_share, annot=True, fmt=".0f", cmap="Blues")
plt.title("% of each symptom group in each urgency class")
save_figure("4_symptom_groups_by_urgency.png")

print("\n=== Average age per urgency class ===")
print(df.groupby(TARGET_COLUMN)["age"].mean().round(1))

print("\n=== % urgency by gender ===")
print((df.groupby("gender")[TARGET_COLUMN].value_counts(normalize=True).unstack(fill_value=0)[URGENCY_ORDER] * 100).round(0))

print("\n=== % urgency by comorbidity ===")
print(comorbidity_share.round(0))

print("\n=== % urgency by symptom group ===")
print(symptom_share.round(0))