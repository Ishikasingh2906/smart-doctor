from predict import get_input_options, get_symptom_groups, predict_priority, predict_urgency

sample_patient = {
    "age": 45,
    "gender": "Female",
    "comorbidities": "Hypertension",
    "symptom_1": "fever",
    "symptom_2": "stomach pain",
    "symptom_3": "weakness",
}

print("=== Allowed options for the questionnaire ===")
for field, options in get_input_options().items():
    print(field, "->", options)

print("\n=== Symptom groups (first 2 of", len(get_symptom_groups()), ") ===")
print(get_symptom_groups()[:2])

print("\n=== Full prediction ===")
print(predict_urgency(sample_patient))

print("\n=== Label only ===")
print(predict_priority(sample_patient))

print("\n=== Invalid input is rejected with a clear message ===")
invalid_patient = dict(sample_patient, age=500)
try:
    predict_urgency(invalid_patient)
except ValueError as error:
    print("ValueError:", error)