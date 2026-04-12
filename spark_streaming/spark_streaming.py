import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, to_timestamp, current_timestamp, split
from pyspark.sql.types import StructType, StructField, StringType, FloatType, LongType
from anomaly_detection import detect_anomalies, refresh_models
from ace_prediction import predict_ace, refresh_ace_models


def process_batch(df, epoch_id):
    if df.isEmpty():
        return

    # Periodically reload models and cohort mappings from storage
    if epoch_id % 100 == 0:
        refresh_models()
        refresh_ace_models()

    # Stage 1: Anomaly detection (groups by device_id, looks up cohort model)
    anomaly_df = detect_anomalies(df)

    # Stage 2: ACE risk prediction
    result_df = predict_ace(anomaly_df)

    # Output anomalies
    anomalies = result_df.filter(col("is_anomaly"))
    if not anomalies.isEmpty():
        print(f"Anomalies detected in batch {epoch_id}:")
        anomalies.show(truncate=False)

    # Output high ACE risk scores
    high_risk = result_df.filter(col("ace_risk_score") > 0.7)
    if not high_risk.isEmpty():
        print(f"High ACE risk in batch {epoch_id}:")
        high_risk.show(truncate=False)


def main():
    spark = SparkSession.builder \
        .appName("IoTStreamingAnomalyDetection") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("ERROR")

    # Schema: device_id is now a region-prefixed UUID string
    schema = StructType([
        StructField("device_id", StringType()),
        StructField("timestamp", LongType()),
        StructField("temperature", FloatType()),
        StructField("humidity", FloatType()),
        StructField("pressure", FloatType())
    ])

    kafka_broker = os.getenv("KAFKA_BROKER", "localhost:9092")

    df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_broker) \
        .option("subscribe", "iot-data") \
        .option("startingOffsets", "latest") \
        .option("maxOffsetsPerTrigger", "100000") \
        .load()

    # Parse JSON payload
    parsed_df = df.select(
        from_json(col("value").cast("string"), schema).alias("data")
    ).select("data.*")

    # Add server-side ingest timestamp (independent of device clock)
    parsed_df = parsed_df.withColumn("ingest_timestamp", current_timestamp())

    # Convert device timestamp to proper timestamp type
    parsed_df = parsed_df.withColumn("device_timestamp", to_timestamp(col("timestamp")))

    # Extract region from device_id (format: "region/d-uuid")
    parsed_df = parsed_df.withColumn("region", split(col("device_id"), "/")[0])

    # Watermark on ingest_timestamp to handle late-arriving data (24h window)
    parsed_df = parsed_df.withWatermark("ingest_timestamp", "24 hours")

    # Process the streaming data
    query = parsed_df \
        .writeStream \
        .foreachBatch(process_batch) \
        .outputMode("update") \
        .start()

    query.awaitTermination()


if __name__ == "__main__":
    main()
