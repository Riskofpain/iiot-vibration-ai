from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.compute import Server
from diagrams.onprem.database import Influxdb
from diagrams.onprem.monitoring import Grafana
# ZMIANA: Używamy RabbitMQ jako symbolu Brokera Wiadomości
from diagrams.onprem.queue import RabbitMQ 
from diagrams.programming.language import Python
from diagrams.generic.device import Tablet
from diagrams.generic.device import Tablet, Mobile

# Kolory i style
graph_attr = {
    "fontsize": "20",
    "bgcolor": "transparent"
}

with Diagram("Industrial IoT Vibration Analysis - Architecture", show=False, filename="architecture_diagram", graph_attr=graph_attr, direction="LR"):
    
    with Cluster("Physical Layer"):
        sensor = Mobile("ESP32 + MPU6050\n(WiFi Sensor)")
        machine = Tablet("Industrial Fan\n(Data Source)")
        machine >> Edge(label="Vibrations") >> sensor

    with Cluster("Docker Container Stack (Debian Edge Device)"):
        
        with Cluster("Communication"):
            # ZMIANA: RabbitMQ udaje Mosquitto (funkcja ta sama - Broker)
            mqtt = RabbitMQ("Mosquitto Broker\n(Port 1883)")
        
        with Cluster("Processing Core"):
            worker = Python("AI Worker\n(Isolation Forest Model)")
        
        with Cluster("Storage & Visualization"):
            influx = Influxdb("InfluxDB v2\n(Time-Series Data)")
            grafana = Grafana("Grafana Dashboard\n(Port 3000)")

    # Główne przepływy danych
    sensor >> Edge(color="firebrick", style="dashed", label="MQTT JSON\n(Raw Data)") >> mqtt
    mqtt >> Edge(color="darkgreen", label="Subscribed Data") >> worker
    worker >> Edge(label="Processed Data\n+ AI Prediction") >> influx
    influx >> Edge(label="Query Data") >> grafana

print("Diagram wygenerowany jako architecture_diagram.png")
