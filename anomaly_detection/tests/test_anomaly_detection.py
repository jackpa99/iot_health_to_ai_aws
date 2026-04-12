import unittest

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    BooleanType, FloatType, IntegerType, LongType, StructField, StructType,
)

from anomaly_detection import detect_anomalies


class TestAnomalyDetection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spark = (
            SparkSession.builder.appName("TestAnomalyDetection")
            .master("local[2]")
            .config("spark.sql.execution.arrow.pyspark.enabled", "true")
            .getOrCreate()
        )

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()

    def test_detect_anomalies(self):
        schema = StructType(
            [
                StructField("device_id", IntegerType()),
                StructField("timestamp", LongType()),
                StructField("temperature", FloatType()),
                StructField("humidity", FloatType()),
                StructField("pressure", FloatType()),
            ]
        )
        data = [
            (0, 1625097600, 25.0, 50.0, 1000.0), (0, 1625097601, 25.5, 51.0, 1001.0),
            (0, 1625097602, 26.0, 52.0, 1002.0), (0, 1625097603, 50.0, 90.0, 900.0),
            (1, 1625097600, 24.0, 49.0, 998.0),  (1, 1625097601, 24.5, 50.0, 999.0),
            (1, 1625097602, 25.0, 51.0, 1000.0), (1, 1625097603, 0.0, 10.0, 1100.0),
        ]
        df = self.spark.createDataFrame(data, schema)
        result_df = detect_anomalies(df)

        self.assertIn("is_anomaly", result_df.columns)
        self.assertEqual(result_df.schema["is_anomaly"].dataType, BooleanType())
        anomalies = result_df.filter("is_anomaly").collect()
        self.assertEqual(len(anomalies), 2)


if __name__ == "__main__":
    unittest.main()
