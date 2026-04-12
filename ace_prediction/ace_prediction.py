import logging
from functools import lru_cache
from model_storage import load_model, load_cohort_mapping

logger = logging.getLogger("ace_prediction")

# Cohort mapping: device_id -> cohort_id
_cohort_mapping: dict | None = None


def _get_cohort_mapping() -> dict:
    global _cohort_mapping
    if _cohort_mapping is None:
        try:
            _cohort_mapping = load_cohort_mapping()
        except (FileNotFoundError, OSError):
            _cohort_mapping = {}
    return _cohort_mapping


@lru_cache(maxsize=500)
def _get_ace_model(cohort_id: str):
    """Load ACE model for a cohort. LRU-cached (max 500 entries)."""
    try:
        model = load_model("ace", cohort_id)
        logger.info("Loaded ACE model for cohort %s", cohort_id)
        return model
    except (FileNotFoundError, OSError):
        logger.warning("No ACE model for cohort %s", cohort_id)
        return None


def refresh_ace_models():
    """Clear caches so models and mapping are reloaded on next use."""
    global _cohort_mapping
    _cohort_mapping = None
    _get_ace_model.cache_clear()


def predict_ace(df):
    """Add ACE risk prediction to a DataFrame that already has anomaly results.

    Requires PySpark — imported lazily so model cache logic is testable
    without a Spark installation.
    """
    from pyspark.sql.types import StructType, StructField, StringType, FloatType, BooleanType

    feature_cols = ["temperature", "humidity", "pressure"]

    output_schema = StructType([
        StructField("device_id", StringType()),
        StructField("temperature", FloatType()),
        StructField("humidity", FloatType()),
        StructField("pressure", FloatType()),
        StructField("is_anomaly", BooleanType()),
        StructField("ace_risk_score", FloatType()),
    ])

    def predict_device_ace(pdf):
        device_id = str(pdf["device_id"].iloc[0])
        mapping = _get_cohort_mapping()
        cohort_id = mapping.get(device_id)

        model = _get_ace_model(cohort_id) if cohort_id else None

        result_pdf = pdf[["device_id"] + feature_cols + ["is_anomaly"]].copy()
        if model is None:
            result_pdf["ace_risk_score"] = 0.0
        else:
            result_pdf["ace_risk_score"] = model.predict_proba(
                pdf[feature_cols]
            )[:, 1].astype(float)
        return result_pdf

    return df.groupBy("device_id").applyInPandas(predict_device_ace, schema=output_schema)
