# tests/test_anomaly_detection.py
import unittest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, IntegerType, FloatType, LongType, BooleanType
from anomaly_detection import detect_anomalies

class TestAnomalyDetection(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.spark = SparkSession.builder.appName("TestAnomalyDetection").master("local[2]").getOrCreate()

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()

    def test_detect_anomalies(self):
        # Create a sample DataFrame
        schema = StructType([
            StructField("device_id", IntegerType()),
            StructField("timestamp", LongType()),
            StructField("temperature", FloatType()),
            StructField("humidity", FloatType()),
            StructField("pressure", FloatType())
        ])

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

        df = self.spark.createDataFrame(data, schema)

        # Run anomaly detection
        result_df = detect_anomalies(df)

        # Check if the result DataFrame has the expected schema
        expected_schema = StructType(schema.fields + [StructField("is_anomaly", BooleanType())])
        self.assertEqual(result_df.schema, expected_schema)

        # Check if anomalies are correctly identified
        anomalies = result_df.filter(result_df.is_anomaly).collect()
        self.assertEqual(len(anomalies), 2)
        self.assertEqual(anomalies[0]['device_id'], 0)
        self.assertEqual(anomalies[0]['temperature'], 50.0)
        self.assertEqual(anomalies[1]['device_id'], 1)
        self.assertEqual(anomalies[1]['temperature'], 0.0)

if __name__ == '__main__':
    unittest.main()