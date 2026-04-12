import os
import hashlib
import json
import joblib
import fsspec


def get_filesystem():
    """Return an fsspec filesystem configured from environment variables.

    Supports any S3-compatible backend (AWS S3, MinIO, Ceph) via the
    S3_ENDPOINT_URL variable.  Falls back to the local filesystem when
    MODEL_STORAGE_URI does not start with "s3://".
    """
    endpoint_url = os.getenv("S3_ENDPOINT_URL", "")
    access_key = os.getenv("S3_ACCESS_KEY", "")
    secret_key = os.getenv("S3_SECRET_KEY", "")

    storage_uri = os.getenv("MODEL_STORAGE_URI", "/tmp/models/")
    if storage_uri.startswith("s3://"):
        return fsspec.filesystem(
            "s3",
            endpoint_url=endpoint_url,
            key=access_key,
            secret=secret_key,
        )
    return fsspec.filesystem("file")


def _base_path() -> str:
    base = os.getenv("MODEL_STORAGE_URI", "/tmp/models/")
    if base.startswith("s3://"):
        base = base[len("s3://"):]
    return base.rstrip("/")


def _hash_prefix(entity_id: str) -> str:
    """2-char hex prefix for S3 partition distribution."""
    return hashlib.md5(entity_id.encode()).hexdigest()[:2]


def _model_path(model_type: str, entity_id: str) -> str:
    """Build the full path for a model artifact.

    Uses a hash prefix to distribute objects across S3 partitions,
    preventing hot-prefix throttling at scale.
    """
    prefix = _hash_prefix(entity_id)
    return f"{_base_path()}/{model_type}/{prefix}/cohort_{entity_id}/latest.joblib"


def save_model(model, model_type: str, entity_id: str) -> str:
    """Serialize *model* to the configured object store."""
    fs = get_filesystem()
    path = _model_path(model_type, entity_id)
    fs.mkdirs(os.path.dirname(path), exist_ok=True)
    with fs.open(path, "wb") as f:
        joblib.dump(model, f)
    return path


def load_model(model_type: str, entity_id: str):
    """Load a model from the configured object store."""
    fs = get_filesystem()
    path = _model_path(model_type, entity_id)
    with fs.open(path, "rb") as f:
        return joblib.load(f)


# --- Cohort mapping persistence ---

def _cohort_mapping_path() -> str:
    return f"{_base_path()}/cohort_mapping.json"


def _kmeans_model_path() -> str:
    return f"{_base_path()}/cohort_kmeans.joblib"


def save_cohort_mapping(mapping: dict) -> str:
    """Save device_id → cohort_id mapping as JSON."""
    fs = get_filesystem()
    path = _cohort_mapping_path()
    fs.mkdirs(os.path.dirname(path), exist_ok=True)
    with fs.open(path, "w") as f:
        json.dump(mapping, f)
    return path


def load_cohort_mapping() -> dict:
    """Load device_id → cohort_id mapping from storage."""
    fs = get_filesystem()
    path = _cohort_mapping_path()
    with fs.open(path, "r") as f:
        return json.load(f)


def save_kmeans_model(model) -> str:
    """Save the KMeans clustering model."""
    fs = get_filesystem()
    path = _kmeans_model_path()
    fs.mkdirs(os.path.dirname(path), exist_ok=True)
    with fs.open(path, "wb") as f:
        joblib.dump(model, f)
    return path


def load_kmeans_model():
    """Load the KMeans clustering model."""
    fs = get_filesystem()
    path = _kmeans_model_path()
    with fs.open(path, "rb") as f:
        return joblib.load(f)
