from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

# Create Spark session
spark = SparkSession.builder \
    .appName("IoTDataProcessing") \
    .getOrCreate()

# Define schema for the Kafka messages
schema = StructType([
    StructField("device_id", StringType(), True),
    StructField("timestamp", StringType(), True),
    StructField("heart_rate", DoubleType(), True),
    StructField("blood_pressure", StringType(), True),
    StructField("temperature", DoubleType(), True)
])

# Read from Kafka
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "YOUR_MSK_BROKERS") \
    .option("subscribe", "iot-data") \
    .load()

# Parse JSON data
parsed_df = df.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")

# Write to S3 as Parquet
query = parsed_df \
    .writeStream \
    .outputMode("append") \
    .format("parquet") \
    .option("path", "s3://your-bucket-parquet-data/") \
    .option("checkpointLocation", "s3://your-bucket-checkpoints/") \
    .partitionBy("device_id") \
    .trigger(processingTime="1 minute") \
    .start()

query.awaitTermination()
