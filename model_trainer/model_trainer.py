import os
import time
import logging

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from kafka import KafkaConsumer
import json

from model_storage import save_model, save_cohort_mapping, save_kmeans_model
from cohort import compute_cohorts

logger = logging.getLogger("model_trainer")

FEATURES = ["temperature", "humidity", "pressure"]


def train_anomaly_models(df: pd.DataFrame, cohort_mapping: dict):
    """Train one IsolationForest per cohort."""
    df = df.copy()
    df["cohort_id"] = df["device_id"].astype(str).map(cohort_mapping)
    cohort_ids = df["cohort_id"].dropna().unique()

    for cohort_id in cohort_ids:
        cohort_df = df[df["cohort_id"] == cohort_id]
        X = cohort_df[FEATURES]
        if len(X) < 20:
            logger.warning("Cohort %s has only %d samples, skipping", cohort_id, len(X))
            continue

        train, _ = train_test_split(X, test_size=0.2, random_state=42)
        model = IsolationForest(contamination=0.1, random_state=42)
        model.fit(train)
        save_model(model, "anomaly", str(cohort_id))

    logger.info("Anomaly models trained for %d cohorts.", len(cohort_ids))


def generate_ace_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Generate synthetic ACE risk labels from telemetry thresholds.

    In production, replace this with clinician-labeled data.
    """
    df = df.copy()
    df["target"] = (
        (df["temperature"] > 28) | (df["temperature"] < 22)
        | (df["humidity"] > 58) | (df["humidity"] < 42)
        | (df["pressure"] > 1008) | (df["pressure"] < 992)
    ).astype(int)
    return df


def train_ace_models(df: pd.DataFrame, cohort_mapping: dict):
    """Train one RandomForestClassifier per cohort for ACE prediction."""
    labeled_df = generate_ace_labels(df)
    labeled_df["cohort_id"] = labeled_df["device_id"].astype(str).map(cohort_mapping)
    cohort_ids = labeled_df["cohort_id"].dropna().unique()

    for cohort_id in cohort_ids:
        cohort_df = labeled_df[labeled_df["cohort_id"] == cohort_id]
        X = cohort_df[FEATURES]
        y = cohort_df["target"]
        if len(X) < 20 or y.nunique() < 2:
            logger.warning("Cohort %s insufficient for ACE training, skipping", cohort_id)
            continue

        X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestClassifier(random_state=42)
        model.fit(X_train, y_train)
        save_model(model, "ace", str(cohort_id))

    logger.info("ACE models trained for %d cohorts.", len(cohort_ids))


def train_models(df: pd.DataFrame, n_cohorts: int = 200):
    """Train all model types using cohort-based clustering.

    1. Cluster devices into cohorts via KMeans
    2. Save cohort mapping + KMeans model
    3. Train anomaly + ACE models per cohort
    """
    kmeans_model, cohort_mapping = compute_cohorts(df, n_cohorts=n_cohorts)
    save_cohort_mapping(cohort_mapping)
    save_kmeans_model(kmeans_model)
    logger.info("Cohort mapping saved: %d devices -> %d cohorts",
                len(cohort_mapping), len(set(cohort_mapping.values())))

    train_anomaly_models(df, cohort_mapping)
    train_ace_models(df, cohort_mapping)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "iot-data")
    KAFKA_BOOTSTRAP_SERVERS = [os.getenv("KAFKA_BROKER", "localhost:9092")]
    CONSUME_DURATION = int(os.getenv("CONSUME_DURATION_SECONDS", "300"))
    MAX_MESSAGES = int(os.getenv("MAX_MESSAGES", "5000000"))
    N_COHORTS = int(os.getenv("N_COHORTS", "200"))

    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="model_trainer_group",
        consumer_timeout_ms=10000,
    )

    data = []
    deadline = time.time() + CONSUME_DURATION
    logger.info("Consuming from %s for up to %ds...", KAFKA_TOPIC, CONSUME_DURATION)

    for message in consumer:
        data.append(message.value)
        if len(data) >= MAX_MESSAGES or time.time() > deadline:
            break

    consumer.close()
    logger.info("Consumed %d messages.", len(data))

    if len(data) < 100:
        logger.warning("Insufficient data (%d msgs), skipping training.", len(data))
    else:
        df = pd.DataFrame(data)
        train_models(df, n_cohorts=N_COHORTS)
