"""Per-device anomaly detection on Spark DataFrames using Isolation Forest.

Spark 3.0 deprecated ``pandas_udf(PandasUDFType.GROUPED_MAP)`` + ``groupBy().apply(udf)``
in favor of ``GroupedData.applyInPandas(func, schema)``. Modern Spark (3.3+) no longer
supports the old grouped-map pandas_udf shape cleanly, so we migrate here.
"""
from __future__ import annotations

import pandas as pd
from pyspark.sql import DataFrame
from pyspark.sql.types import (
    BooleanType,
    FloatType,
    IntegerType,
    LongType,
    StructField,
    StructType,
)
from sklearn.ensemble import IsolationForest

FEATURE_COLS = ("temperature", "humidity", "pressure")


def _output_schema(has_timestamp: bool) -> StructType:
    fields = [StructField("device_id", IntegerType())]
    if has_timestamp:
        fields.append(StructField("timestamp", LongType()))
    fields += [
        StructField("temperature", FloatType()),
        StructField("humidity", FloatType()),
        StructField("pressure", FloatType()),
        StructField("is_anomaly", BooleanType()),
    ]
    return StructType(fields)


def _detect_for_group(pdf: pd.DataFrame) -> pd.DataFrame:
    model = IsolationForest(contamination=0.1, random_state=42)
    X = pdf[list(FEATURE_COLS)]
    # Isolation Forest requires >=2 samples; short windows get all-normal.
    if len(X) < 2:
        pdf = pdf.copy()
        pdf["is_anomaly"] = False
        return pdf
    model.fit(X)
    pdf = pdf.copy()
    pdf["is_anomaly"] = model.predict(X) == -1
    return pdf


def detect_anomalies(df: DataFrame) -> DataFrame:
    """Return *df* with an added ``is_anomaly`` boolean column, per-device.

    Uses ``applyInPandas`` (Spark 3.0+) -- the supported replacement for the
    deprecated ``pandas_udf(GROUPED_MAP)`` + ``groupBy.apply`` pattern.
    """
    has_timestamp = "timestamp" in df.columns
    schema = _output_schema(has_timestamp)
    return df.groupBy("device_id").applyInPandas(_detect_for_group, schema=schema)


if __name__ == "__main__":  # pragma: no cover
    from pyspark.sql import SparkSession

    spark = SparkSession.builder.appName("AnomalyDetection").getOrCreate()
    data = [
        (0, 1625097600, 25.0, 50.0, 1000.0),
        (0, 1625097603, 50.0, 90.0, 900.0),
        (1, 1625097600, 24.0, 49.0, 998.0),
        (1, 1625097603, 0.0, 10.0, 1100.0),
    ]
    df = spark.createDataFrame(
        data, ["device_id", "timestamp", "temperature", "humidity", "pressure"]
    )
    detect_anomalies(df).show()
    spark.stop()
