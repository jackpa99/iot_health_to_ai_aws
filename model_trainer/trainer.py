"""Consume IoT telemetry from Kafka and train a per-device Isolation Forest.

Cloud-portable by design: model artifacts are written to a URI resolved by
``fsspec`` (file:// / s3:// / gs:// / abfs:// / http(s):// / hdfs://). Set
``MODEL_STORAGE_URI`` to choose the backend. Credentials come from whatever
the host environment provides -- typically K8s Secrets materialized by the
External Secrets Operator -- and are read directly by the fsspec backend
(e.g. s3fs honors ``AWS_ACCESS_KEY_ID`` / ``AWS_SECRET_ACCESS_KEY`` /
``S3_ENDPOINT_URL`` for any S3-compatible store).
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

import fsspec
import joblib
import pandas as pd
from kafka import KafkaConsumer
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)

KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "iot-data")
KAFKA_BOOTSTRAP_SERVERS: list[str] = os.getenv("KAFKA_BROKER", "localhost:9092").split(",")
MODEL_STORAGE_URI = os.getenv("MODEL_STORAGE_URI", "file:///tmp/models")
FEATURES = ("temperature", "humidity", "pressure")


def _fsspec_storage_options() -> dict[str, Any]:
    """Pass-through options that fsspec backends honor.

    s3fs (and other S3-compatible clients) read ``S3_ENDPOINT_URL`` to point at
    MinIO / Ceph RGW / corp S3. We surface it explicitly so the config is visible
    at the call site, rather than relying on implicit env reads.
    """
    opts: dict[str, Any] = {}
    endpoint = os.getenv("S3_ENDPOINT_URL")
    if endpoint:
        opts["client_kwargs"] = {"endpoint_url": endpoint}
    return opts


def consume_training_data(limit: int = 10_000) -> pd.DataFrame:
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="model_trainer_group",
    )
    try:
        rows: list[dict] = []
        for message in consumer:
            rows.append(message.value)
            if len(rows) >= limit:
                break
    finally:
        consumer.close()
    return pd.DataFrame(rows)


def train_models(df: pd.DataFrame, storage_uri: str = MODEL_STORAGE_URI) -> list[str]:
    """Train one IsolationForest per device_id; return the artifact URIs written.

    *storage_uri* may point at any fsspec-supported backend
    (file://, s3://, gs://, abfs://, http://, hdfs://...).
    """
    fs, base = fsspec.core.url_to_fs(storage_uri, **_fsspec_storage_options())
    # Most backends no-op on makedirs; local filesystems need it.
    try:
        fs.makedirs(base, exist_ok=True)
    except (FileExistsError, NotImplementedError):
        pass

    written: list[str] = []
    for device in df["device_id"].unique():
        device_df = df[df["device_id"] == device]
        X = device_df[list(FEATURES)]
        train, _test = train_test_split(X, test_size=0.2, random_state=42)
        model = IsolationForest(contamination=0.1, random_state=42)
        model.fit(train)
        out_path = f"{base.rstrip('/')}/model_device_{device}.joblib"
        with fs.open(out_path, "wb") as fh:
            joblib.dump(model, fh)
        written.append(out_path)
    logger.info("Trained %d device models at %s", len(written), storage_uri)
    return written


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    df = consume_training_data()
    train_models(df)


if __name__ == "__main__":
    main()
