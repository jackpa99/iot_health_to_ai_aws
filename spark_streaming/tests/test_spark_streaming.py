import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, FloatType, TimestampType
import spark_streaming

@pytest.fixture(scope="module")
def spark():
    return SparkSession.builder.master("local[2]").appName("test").getOrCreate()

def test_data_processing(spark):
    # Create a sample dataframe
    schema = StructType([
        StructField("device_id", StringType()),
        StructField("timestamp", TimestampType()),
        StructField("temperature", FloatType()),
        StructField("humidity", FloatType()),
        StructField("pressure", FloatType())
    ])
    
    data = [
        ("device_1", "2023-05-01 10:00:00", 25.5, 60.0, 1013.0),
        ("device_1", "2023-05-01 10:01:00", 26.0, 61.0, 1012.5),
        ("device_2", "2023-05-01 10:00:00", 24.5, 59.0, 1014.0)
    ]
    
    df = spark.createDataFrame(data, schema)
    
    # Process the data
    result_df = df.groupBy("device_id").agg({
        "temperature": "avg",
        "humidity": "avg",
        "pressure": "avg"
    })
    
    # Check the results
    result = result_df.collect()
    assert len(result) == 2
    
    device_1 = next(row for row in result if row["device_id"] == "device_1")
    assert device_1["avg(temperature)"] == pytest.approx(25.75)
    assert device_1["avg(humidity)"] == pytest.approx(60.5)
    assert device_1["avg(pressure)"] == pytest.approx(1012.75)
    
    device_2 = next(row for row in result if row["device_id"] == "device_2")
    assert device_2["avg(temperature)"] == pytest.approx(24.5)
    assert device_2["avg(humidity)"] == pytest.approx(59.0)
    assert device_2["avg(pressure)"] == pytest.approx(1014.0)