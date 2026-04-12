"""Spark Structured Streaming job: read IoT telemetry from Kafka and flag anomalies."""
from __future__ import annotations

import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, timestamp_seconds
from pyspark.sql.types import StructType, StructField, IntegerType, FloatType, LongType

from anomaly_detection import detect_anomalies

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "iot-data")


def process_batch(df, epoch_id: int) -> None:
    anomaly_df = detect_anomalies(df)
    anomalies = anomaly_df.filter(col("is_anomaly"))
    # DataFrame.isEmpty() is available in Spark 3.3+
    if not anomalies.isEmpty():
        print(f"Anomalies detected in batch {epoch_id}:")  # noqa: T201
        anomalies.show(truncate=False)


def main() -> None:
    spark = (
        SparkSession.builder.appName("IoTStreamingAnomalyDetection").getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")

    schema = StructType(
        [
            StructField("device_id", IntegerType()),
            StructField("timestamp", LongType()),
            StructField("temperature", FloatType()),
            StructField("humidity", FloatType()),
            StructField("pressure", FloatType()),
        ]
    )

    df = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("subscribe", KAFKA_TOPIC)
        .option("startingOffsets", "latest")
        .load()
    )

    parsed_df = df.select(
        from_json(col("value").cast("string"), schema).alias("data")
    ).select("data.*")

    # Incoming `timestamp` is an epoch-seconds LongType. Use timestamp_seconds
    # (Spark 3.1+) -- to_timestamp on a numeric column is undefined in modern Spark.
    parsed_df = parsed_df.withColumn("timestamp", timestamp_seconds(col("timestamp")))

    query = (
        parsed_df.writeStream.foreachBatch(process_batch)
        .outputMode("update")
        .option("checkpointLocation", os.getenv("CHECKPOINT_DIR", "/tmp/iot-ckpt"))
        .start()
    )
    query.awaitTermination()


if __name__ == "__main__":
    main()
