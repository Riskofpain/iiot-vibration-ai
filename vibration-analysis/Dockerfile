FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Uruchomienie skryptu z buforowaniem wyjścia (żeby widziec logi w docker logs)
CMD ["python", "-u", "main.py"]
