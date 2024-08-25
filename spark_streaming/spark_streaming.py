# To run this script, you need to ensure that:

# Kafka is running and the "iot-data" topic exists.
# The IoT simulator is running and sending data to the "iot-data" Kafka topic.
# You have all the necessary dependencies installed (PySpark, Kafka-Python, etc.).
# You can run the script using:

# spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2 spark_streaming.py

#The spark-submit command would typically be run from the command line (terminal or command prompt) on the machine where you want to execute the Spark job. The location from which you run this command depends on your setup and deployment strategy. Here are a few common scenarios:

#Local Development:
#If you're developing and testing locally, you would run this command from the directory where your spark_streaming.py file is located. Make sure you have Spark installed locally and the spark-submit command is in your system PATH.
#Cluster Node:
#If you're running on a Spark cluster, you might SSH into one of the cluster nodes (often the master node) and run the command from there. The exact node would depend on your cluster configuration.
#Edge Node:
#In some Hadoop/Spark cluster setups, there's an "edge node" or "gateway node" that's used for submitting jobs to the cluster. You would connect to this node and run the command from there.
#Container or Virtual Machine:
#If you're using containerization (like Docker) or virtual machines, you would run this command inside the container or VM where Spark is installed.
#Cloud Environment:
#If you're using a cloud service like AWS EMR, Google Dataproc, or Azure HDInsight, you might submit this job through their respective interfaces or connect to a master node to run this command.
#Automated CI/CD Pipeline:
#In a production environment, this command might be part of a CI/CD pipeline, executed automatically upon certain triggers (e.g., code commits, scheduled runs).
#Regardless of where you run it from, ensure that:

#Spark is properly installed and configured in that environment.
#The spark_streaming.py file is available in the current directory or provide the full path to the file.
#The Kafka cluster is reachable from where you're running the Spark job.
#Any additional dependencies (like the anomaly_detection.py file) are in the correct locations or included in the Spark job's Python path.
#When deploying to production, you would typically set up a more robust system for job submission and monitoring, possibly using tools like Apache Airflow, Kubernetes, or cloud-specific orchestration services.

from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, to_timestamp
from pyspark.sql.types import StructType, StructField, IntegerType, FloatType, LongType
from anomaly_detection import detect_anomalies

def process_batch(df, epoch_id):
    # Perform anomaly detection
    anomaly_df = detect_anomalies(df)
    
    # Filter out the anomalies
    anomalies = anomaly_df.filter(anomaly_df.is_anomaly == True)
    
    # Write anomalies to console (in a production environment, you might want to save this to a database or send alerts)
    if not anomalies.isEmpty():
        print(f"Anomalies detected in batch {epoch_id}:")
        anomalies.show(truncate=False)
    
    # You can add more processing here, such as aggregations or saving to a database

def main():
    # Create Spark Session
    spark = SparkSession.builder \
        .appName("IoTStreamingAnomalyDetection") \
        .getOrCreate()

    # Set log level to ERROR to reduce console output
    spark.sparkContext.setLogLevel("ERROR")

    # Define schema for incoming data
    schema = StructType([
        StructField("device_id", IntegerType()),
        StructField("timestamp", LongType()),
        StructField("temperature", FloatType()),
        StructField("humidity", FloatType()),
        StructField("pressure", FloatType())
    ])

    # Create streaming DataFrame from Kafka
    df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "localhost:9092") \
        .option("subscribe", "iot-data") \
        .load()

    # Parse JSON data
    parsed_df = df.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")

    # Convert timestamp to proper timestamp type
    parsed_df = parsed_df.withColumn("timestamp", to_timestamp(col("timestamp")))

    # Process the streaming data
    query = parsed_df \
        .writeStream \
        .foreachBatch(process_batch) \
        .outputMode("update") \
        .start()

    # Wait for the streaming to finish
    query.awaitTermination()

if __name__ == "__main__":
    main()