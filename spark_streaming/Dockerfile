FROM apache/spark:3.5.3-python3

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY spark_streaming.py .
COPY ../anomaly_detection/anomaly_detection.py ./anomaly_detection.py

CMD ["spark-submit", \
     "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3", \
     "spark_streaming.py"]
