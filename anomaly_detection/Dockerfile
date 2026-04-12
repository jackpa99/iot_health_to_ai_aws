FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY anomaly_detection.py .
COPY model_storage.py .

CMD ["python", "anomaly_detection.py"]
