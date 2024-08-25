# tests/test_spark_streaming.py
import unittest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, IntegerType, FloatType, LongType
from pyspark.sql.functions import from_json, col

class TestSparkStreaming(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.spark = SparkSession.builder.appName("TestIoTStreaming").master("local[2]").getOrCreate()

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()

    def test_schema(self):
        # Define the expected schema
        expected_schema = StructType([
            StructField("device_id", IntegerType()),
            StructField("timestamp", LongType()),
            StructField("temperature", FloatType()),
            StructField("humidity", FloatType()),
            StructField("pressure", FloatType())
        ])

        # Create a sample DataFrame with the expected schema
        data = [
            ('{"device_id": 1, "timestamp": 1625097600, "temperature": 25.5, "humidity": 50.0, "pressure": 1000.0}',)
        ]
        df = self.spark.createDataFrame(data, ["value"])

        # Parse the JSON data
        parsed_df = df.select(from_json(col("value").cast("string"), expected_schema).alias("data")).select("data.*")

        # Check if the parsed DataFrame has the expected schema
        self.assertEqual(parsed_df.schema, expected_schema)

        # Check if the data is correctly parsed
        row = parsed_df.collect()[0]
        self.assertEqual(row['device_id'], 1)
        self.assertEqual(row['timestamp'], 1625097600)
        self.assertEqual(row['temperature'], 25.5)
        self.assertEqual(row['humidity'], 50.0)
        self.assertEqual(row['pressure'], 1000.0)

if __name__ == '__main__':
    unittest.main()