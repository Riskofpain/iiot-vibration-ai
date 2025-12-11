import paho.mqtt.client as mqtt
import json
import csv
import os

MQTT_BROKER = "localhost"
MQTT_TOPIC = "factory/line1/fan01/vibration/raw"
FILENAME = "training_data.csv"

# Nie pytamy już o etykietę. Zakładamy, że nagrywasz ZDROWĄ maszynę.
print("--- NAGRYWANIE WZORCA NORMALNOŚCI ---")
print("Upewnij się, że wiatrak działa POPRAWNIE.")
input("Naciśnij ENTER, aby rozpocząć nagrywanie...")

file_exists = os.path.isfile(FILENAME)
csv_file = open(FILENAME, 'a', newline='')
writer = csv.writer(csv_file)

if not file_exists:
    # Zapisujemy tylko siłę wibracji (możesz dodać osie, jeśli chcesz być dokładniejszy)
    writer.writerow(["strength"])

def on_connect(client, userdata, flags, rc):
    print("Połączono. Zbieram dane...")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        data = json.loads(payload)
        
        # Zapisujemy TYLKO siłę. 
        # Ignorujemy temperaturę (żeby nie fałszowała) i etykiety.
        row = [data['vib_strength']]
        
        writer.writerow(row)
        csv_file.flush()
        print(f"Nagrano: {data['vib_strength']}g")
        
    except Exception as e:
        print(f"Błąd: {e}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(MQTT_BROKER, 1883, 60)
    client.loop_forever()
except KeyboardInterrupt:
    print("\nZatrzymano.")
    csv_file.close()