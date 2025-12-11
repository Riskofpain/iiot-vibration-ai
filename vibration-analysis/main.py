import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import os
import json
import time
import joblib
import pandas as pd

# --- KONFIGURACJA ---
MQTT_BROKER = os.getenv('MQTT_BROKER', 'mosquitto')
MQTT_TOPIC = "factory/line1/fan01/vibration/raw"
MODEL_FILE = "vibration_model.joblib"

# Podniosłem próg do 0.03, żeby wyciąć te małe szumy (0.024), które widziałeś w logach
MIN_VIBRATION_THRESHOLD = 0.03 

# ILE RAZY MUSI WYSTĄPIĆ BŁĄD, ŻEBY ZGŁOSIĆ ALERT?
ALERT_TRIGGER_COUNT = 3

INFLUX_URL = os.getenv('INFLUX_URL', 'http://influxdb2:8086')
INFLUX_TOKEN = os.getenv('INFLUX_TOKEN', 'moj-super-tajny-token-123')
INFLUX_ORG = os.getenv('INFLUX_ORG', 'factory')
INFLUX_BUCKET = os.getenv('INFLUX_BUCKET', 'sensors')

# --- ZMIENNA GLOBALNA DO LICZENIA BŁĘDÓW ---
consecutive_faults = 0 

# --- 1. ŁADOWANIE MODELU AI ---
print(f"Ładowanie modelu AI z pliku: {MODEL_FILE}...")
try:
    model = joblib.load(MODEL_FILE)
    print("Model załadowany pomyślnie! Gotowy do predykcji.")
except Exception as e:
    print(f"BŁĄD KRYTYCZNY: Nie można załadować modelu! {e}")
    while True: time.sleep(10)

influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)

def on_connect(client, userdata, flags, rc):
    print(f"MQTT Połączono! Kod: {rc}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    # Musimy użyć słowa 'global', żeby móc edytować licznik wewnątrz funkcji
    global consecutive_faults 

    try:
        payload = msg.payload.decode()
        data = json.loads(payload)
        current_strength = float(data['vib_strength'])

        # --- 2. LOGIKA DECYZYJNA ---
        # Krok A: Bramka szumu (czy wiatrak w ogóle chodzi?)
        if current_strength < MIN_VIBRATION_THRESHOLD:
            # Wiatrak stoi -> Wszystko OK, resetujemy licznik błędów
            raw_ai_decision = 0 
            consecutive_faults = 0
            # print(f"STOP (Szum: {current_strength:.3f})")
        else:
            # Wiatrak chodzi -> Pytamy AI
            features = pd.DataFrame([[current_strength]], columns=['strength'])
            
            # IsolationForest zwraca: 1 (Norma), -1 (Anomalia)
            ai_result = model.predict(features)[0]
            
            # Tłumaczymy na nasze (0=OK, 1=Awaria)
            if ai_result == 1:
                raw_ai_decision = 0 # OK
            else:
                raw_ai_decision = 1 # AWARIA

            # --- Krok B: FILTROWANIE (Debouncing) ---
            if raw_ai_decision == 1:
                consecutive_faults += 1 # Zwiększ licznik błędów
                print(f"-> Podejrzenie awarii ({consecutive_faults}/{ALERT_TRIGGER_COUNT}) - Wibracja: {current_strength:.3f}g")
            else:
                consecutive_faults = 0 # Jeśli AI powie OK, to zerujemy licznik (musi być ciąg błędów)

        # --- 3. STATUS FINALNY DLA BAZY ---
        # Zgłaszamy awarię (1) TYLKO JEŚLI licznik przekroczył limit
        if consecutive_faults >= ALERT_TRIGGER_COUNT:
            final_status = 1
            print(f"!!! ALARM POTWIERDZONY !!! (Wibracja: {current_strength:.3f}g)")
        else:
            final_status = 0

        # --- 4. ZAPIS DO BAZY ---
        point = Point("vibration_sensor") \
            .tag("location", "line1") \
            .tag("device", "fan01") \
            .field("ax", float(data['ax'])) \
            .field("ay", float(data['ay'])) \
            .field("az", float(data['az'])) \
            .field("strength", current_strength) \
            .field("temperature", float(data['temp'])) \
            .field("prediction", int(final_status)) # Zapisujemy przefiltrowany status

        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)

    except Exception as e:
        print(f"Błąd przetwarzania: {e}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print(f"AI Worker Startuje (Próg szumu: {MIN_VIBRATION_THRESHOLD}g, Filtr: {ALERT_TRIGGER_COUNT} próbek)...")
while True:
    try:
        client.connect(MQTT_BROKER, 1883, 60)
        client.loop_forever()
    except Exception as e:
        print(f"Błąd połączenia: {e}. Czekam 5s...")
        time.sleep(5)