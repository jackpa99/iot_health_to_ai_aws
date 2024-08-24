import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, FloatType, TimestampType

# Use environment variables for configuration
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'kafka:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'iot_data')
CHECKPOINT_LOCATION = os.getenv('CHECKPOINT_LOCATION', '/tmp/checkpoint')
OUTPUT_PATH = os.getenv('OUTPUT_PATH', '/tmp/output')

# Initialize Spark session
spark = SparkSession.builder \
    .appName("IoTDataProcessor") \
    .getOrCreate()

# Define schema for IoT data
schema = StructType([
    StructField("device_id", StringType()),
    StructField("timestamp", TimestampType()),
    StructField("temperature", FloatType()),
    StructField("humidity", FloatType()),
    StructField("pressure", FloatType())
])

# Read from Kafka
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BROKER) \
    .option("subscribe", KAFKA_TOPIC) \
    .load()

# Parse JSON data
parsed_df = df.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")

# Process data (example: calculate averages)
result_df = parsed_df \
    .groupBy("device_id") \
    .agg({"temperature": "avg", "humidity": "avg", "pressure": "avg"})

# Write results to parquet files
query = result_df \
    .writeStream \
    .outputMode("append") \
    .format("parquet") \
    .option("path", OUTPUT_PATH) \
    .option("checkpointLocation", CHECKPOINT_LOCATION) \
    .start()

query.awaitTermination()