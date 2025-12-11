import asyncio
import logging
import random
import math
import json
import time
import paho.mqtt.client as mqtt
from asyncua import Server, ua

# --- KONFIGURACJA MQTT ---
# Wewnątrz sieci Docker kontener nazywa się "mosquitto"
MQTT_BROKER = "mosquitto"
MQTT_PORT = 1883
MQTT_TOPIC = "fabryka/robot1/dane"

def connect_mqtt():
    client = mqtt.Client()
    try:
        # Próba połączenia z brokerem
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start() # Uruchom pętlę w tle
        print(f"[MQTT] Polaczono z brokerem: {MQTT_BROKER}", flush=True)
        return client
    except Exception as e:
        print(f"[MQTT] Blad polaczenia: {e}", flush=True)
        return None

async def main():
    # 1. Start MQTT
    mqtt_client = connect_mqtt()

    # 2. Start OPC UA (Zostawiamy, żeby działało w tle jak profesjonalna maszyna)
    server = Server()
    await server.init()
    server.set_endpoint('opc.tcp://0.0.0.0:4840/freeopcua/server/')
    idx = await server.register_namespace('http://examples.freeopcua.github.io')
    objects = server.nodes.objects
    robot = await objects.add_object(idx, 'Robot_KUKA_KR210')
    
    # Zmienne OPC UA
    temp_node = await robot.add_variable(idx, 'Motor_Temperature', 0.0)
    axis_node = await robot.add_variable(idx, 'Axis_1_Position', 0.0)
    
    print("Start symulacji Robot + MQTT...", flush=True)
    
    async with server:
        count = 0
        while True:
            await asyncio.sleep(1) # Co 1 sekundę
            count += 0.1
            
            # Generowanie danych
            temp = 40 + random.uniform(0, 20)
            pos = math.sin(count) * 100
            
            # Aktualizacja OPC UA
            await temp_node.write_value(temp)
            await axis_node.write_value(pos)
            
            # --- WYSYŁANIE DO MQTT ---
            if mqtt_client:
                # Tworzymy paczkę JSON
                payload = json.dumps({
                    "temperatura": round(temp, 2),
                    "pozycja": round(pos, 2),
                    "status": "Running"
                })
                # Publikujemy
                mqtt_client.publish(MQTT_TOPIC, payload)
                print(f"[MQTT] Wyslano: {payload}", flush=True)
            else:
                print("Brak polaczenia MQTT, probuje ponownie...", flush=True)
                mqtt_client = connect_mqtt()

if __name__ == '__main__':
    asyncio.run(main())
