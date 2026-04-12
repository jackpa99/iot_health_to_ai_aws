FROM apache/spark-py:v3.5.3

WORKDIR /app

COPY spark_streaming/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY spark_streaming/spark_streaming.py .
COPY anomaly_detection/anomaly_detection.py .
COPY ace_prediction/ace_prediction.py .
COPY model_trainer/model_storage.py .

CMD ["spark-submit", \
     "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3", \
     "--driver-memory", "4g", \
     "--executor-memory", "4g", \
     "--executor-cores", "2", \
     "--conf", "spark.sql.shuffle.partitions=200", \
     "--conf", "spark.default.parallelism=200", \
     "spark_streaming.py"]
