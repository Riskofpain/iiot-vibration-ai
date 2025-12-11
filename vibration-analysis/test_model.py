import joblib
import pandas as pd

# Ładujemy Twój obecny model
try:
    model = joblib.load('vibration_model.joblib')
    print("Model załadowany.")
except:
    print("Brak modelu!")
    exit()

# Tworzymy 2 sztuczne sytuacje:
# 1. IDEALNA CISZA (Wibracja 0.02), ale WYSOKA TEMPERATURA (30 stopni)
data_cisza = pd.DataFrame([[0, 0, 0, 0.02, 30.0]], columns=['ax', 'ay', 'az', 'strength', 'temp'])

# 2. TRZĘSIENIE ZIEMI (Wibracja 0.80), ale NISKA TEMPERATURA (20 stopni)
data_awaria = pd.DataFrame([[0, 0, 0, 0.80, 20.0]], columns=['ax', 'ay', 'az', 'strength', 'temp'])

pred_cisza = model.predict(data_cisza)[0]
pred_awaria = model.predict(data_awaria)[0]

print("-" * 30)
print(f"Symulacja CISZA (vib=0.02, temp=30C) -> AI ocenia: {pred_cisza}")
print(f"Symulacja AWARIA (vib=0.80, temp=20C) -> AI ocenia: {pred_awaria}")
print("-" * 30)

if pred_cisza == 1:
    print("WNIOSKI: Model jest zepsuty! Krzyczy AWARIA nawet przy braku wibracji.")
    print("Prawdopodobnie patrzy na temperaturę zamiast na wibracje.")
else:
    print("WNIOSKI: Model działa poprawnie na sucho. Problem jest w main.py.")