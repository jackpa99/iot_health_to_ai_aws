import logging
from functools import lru_cache
from model_storage import load_model, load_cohort_mapping

logger = logging.getLogger("anomaly_detection")

# Cohort mapping: device_id -> cohort_id
_cohort_mapping: dict | None = None


def _get_cohort_mapping() -> dict:
    global _cohort_mapping
    if _cohort_mapping is None:
        try:
            _cohort_mapping = load_cohort_mapping()
            logger.info("Loaded cohort mapping with %d devices", len(_cohort_mapping))
        except (FileNotFoundError, OSError):
            logger.warning("No cohort mapping found")
            _cohort_mapping = {}
    return _cohort_mapping


@lru_cache(maxsize=500)
def _get_model(cohort_id: str):
    """Load anomaly model for a cohort. LRU-cached (max 500 entries)."""
    try:
        model = load_model("anomaly", cohort_id)
        logger.info("Loaded anomaly model for cohort %s", cohort_id)
        return model
    except (FileNotFoundError, OSError):
        logger.warning("No anomaly model for cohort %s", cohort_id)
        return None


def refresh_models():
    """Clear caches so models and mapping are reloaded on next use."""
    global _cohort_mapping
    _cohort_mapping = None
    _get_model.cache_clear()


def detect_anomalies(df):
    from pyspark.sql.types import BooleanType, StructType, StructField, StringType, FloatType

    feature_cols = ["temperature", "humidity", "pressure"]

    output_schema = StructType([
        StructField("device_id", StringType()),
        StructField("temperature", FloatType()),
        StructField("humidity", FloatType()),
        StructField("pressure", FloatType()),
        StructField("is_anomaly", BooleanType())
    ])

    def detect_device_anomalies(pdf):
        device_id = str(pdf["device_id"].iloc[0])
        mapping = _get_cohort_mapping()
        cohort_id = mapping.get(device_id)

        model = _get_model(cohort_id) if cohort_id else None

        if model is None:
            # Fallback: train on current batch (degraded mode)
            from sklearn.ensemble import IsolationForest
            model = IsolationForest(contamination=0.1, random_state=42)
            model.fit(pdf[feature_cols])

        predictions = model.predict(pdf[feature_cols])

        result_pdf = pdf[["device_id"] + feature_cols].copy()
        result_pdf["is_anomaly"] = predictions == -1
        return result_pdf

    return df.groupBy("device_id").applyInPandas(detect_device_anomalies, schema=output_schema)


if __name__ == "__main__":
    from pyspark.sql import SparkSession
    from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType

    spark = SparkSession.builder.appName("AnomalyDetection").getOrCreate()

    data = [
        ("us-east-1/d-aaa001", 1625097600, 25.0, 50.0, 1000.0),
        ("us-east-1/d-aaa001", 1625097601, 25.5, 51.0, 1001.0),
        ("us-east-1/d-aaa001", 1625097602, 50.0, 90.0, 900.0),
        ("eu-west-1/d-bbb002", 1625097600, 24.0, 49.0, 998.0),
        ("eu-west-1/d-bbb002", 1625097601, 0.0, 10.0, 1100.0),
    ]
    schema = StructType([
        StructField("device_id", StringType()),
        StructField("timestamp", IntegerType()),
        StructField("temperature", FloatType()),
        StructField("humidity", FloatType()),
        StructField("pressure", FloatType())
    ])
    df = spark.createDataFrame(data, schema)
    result_df = detect_anomalies(df)
    result_df.show()
    spark.stop()
