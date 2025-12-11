import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib

print("Wczytywanie danych...")
data = pd.read_csv('training_data.csv')

# Uczymy się tylko na kolumnie 'strength'
X = data[['strength']]

print(f"Trening na {len(data)} próbkach zdrowej pracy...")

# ISOLATION FOREST

model = IsolationForest(n_estimators=100, contamination='auto', random_state=42)

# Uwaga: Tutaj nie ma 'y' (etykiet)! Uczymy się tylko na X.
model.fit(X)

print("Model nauczony rozpoznawać 'normalność'.")
joblib.dump(model, 'vibration_model.joblib')
print("Zapisano vibration_model.joblib")