# It defines a detect_anomalies function that takes a DataFrame as input.
#Inside detect_anomalies, it uses a VectorAssembler to combine the feature columns (temperature, humidity, pressure) into a single vector column.
#It defines a pandas UDF (User Defined Function) called detect_device_anomalies. This function:
#Trains an Isolation Forest model on the data for each device.
#Uses the model to predict anomalies.
#Returns a DataFrame with the original features and an additional is_anomaly column.
#The detect_anomalies function then applies this pandas UDF to each device group in the input DataFrame.
#The main block at the end of the script provides a way to test the anomaly detection function independently. It:
#Creates a SparkSession.
#Generates a sample DataFrame with data from two devices, including some anomalies.
#Runs the anomaly detection function on this sample data.
#Displays the results.
#This implementation allows for efficient anomaly detection on a per-device basis, which is crucial when dealing with data from multiple IoT devices. Each device's data is processed independently, allowing for device-specific anomaly detection models.

#To use this in your Spark streaming job, you would call detect_anomalies(parsed_df) on your parsed DataFrame of IoT data. The resulting DataFrame will include an is_anomaly column that you can use for further processing or alerting.

from pyspark.ml.feature import VectorAssembler
from pyspark.ml.clustering import KMeans
from pyspark.sql.functions import udf, pandas_udf, PandasUDFType
from pyspark.sql.types import BooleanType, StructType, StructField, IntegerType, FloatType, BooleanType
import pandas as pd
from sklearn.ensemble import IsolationForest

def detect_anomalies(df):
    # Define the features we'll use for anomaly detection
    feature_cols = ["temperature", "humidity", "pressure"]
    
    # Create a VectorAssembler to combine feature columns into a single vector column
    assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
    vectorized_df = assembler.transform(df)
    
    # Define the schema for the output of our pandas UDF
    output_schema = StructType([
        StructField("device_id", IntegerType()),
        StructField("temperature", FloatType()),
        StructField("humidity", FloatType()),
        StructField("pressure", FloatType()),
        StructField("is_anomaly", BooleanType())
    ])

    @pandas_udf(output_schema, PandasUDFType.GROUPED_MAP)
    def detect_device_anomalies(pdf):
        # Train an Isolation Forest model for this device's data
        model = IsolationForest(contamination=0.1, random_state=42)
        X = pdf[feature_cols]
        model.fit(X)
        
        # Predict anomalies
        anomalies = model.predict(X)
        
        # Create a new dataframe with the results
        result_pdf = pdf[["device_id"] + feature_cols].copy()
        result_pdf["is_anomaly"] = anomalies == -1  # -1 indicates an anomaly in Isolation Forest
        
        return result_pdf

    # Apply the anomaly detection function to each device group
    return vectorized_df.groupBy("device_id").apply(detect_device_anomalies)

# If you want to test the function independently
if __name__ == "__main__":
    from pyspark.sql import SparkSession

    # Create a SparkSession
    spark = SparkSession.builder.appName("AnomalyDetection").getOrCreate()

    # Create a sample DataFrame
    data = [
        (0, 1625097600, 25.0, 50.0, 1000.0),
        (0, 1625097601, 25.5, 51.0, 1001.0),
        (0, 1625097602, 26.0, 52.0, 1002.0),
        (0, 1625097603, 50.0, 90.0, 900.0),  # Anomaly
        (1, 1625097600, 24.0, 49.0, 998.0),
        (1, 1625097601, 24.5, 50.0, 999.0),
        (1, 1625097602, 25.0, 51.0, 1000.0),
        (1, 1625097603, 0.0, 10.0, 1100.0),  # Anomaly
    ]
    schema = StructType([
        StructField("device_id", IntegerType()),
        StructField("timestamp", IntegerType()),
        StructField("temperature", FloatType()),
        StructField("humidity", FloatType()),
        StructField("pressure", FloatType())
    ])
    df = spark.createDataFrame(data, schema)

    # Run anomaly detection
    result_df = detect_anomalies(df)

    # Show the results
    result_df.show()

    # Stop the SparkSession
    spark.stop()