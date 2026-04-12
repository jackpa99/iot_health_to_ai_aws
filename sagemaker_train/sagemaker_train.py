import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import IsolationForest
import joblib
from kafka import KafkaConsumer
import json


def train_models(df):
    """Train a separate IsolationForest model for each device."""
    device_ids = df['device_id'].unique()
    features = ['temperature', 'humidity', 'pressure']

    for device in device_ids:
        device_df = df[df['device_id'] == device]
        X = device_df[features]

        train, test = train_test_split(X, test_size=0.2)

        model = IsolationForest(contamination=0.1, random_state=42)
        model.fit(train)

        joblib.dump(model, f'/tmp/model_device_{device}.joblib')

    print("Training complete. Models saved for each device.")


if __name__ == "__main__":
    # Kafka consumer setup
    KAFKA_TOPIC = 'iot-data'
    KAFKA_BOOTSTRAP_SERVERS = ['localhost:9092']

    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='sagemaker_training_group'
    )

    data = []
    for message in consumer:
        data.append(message.value)
        if len(data) >= 10000:
            break

    df = pd.DataFrame(data)
    train_models(df)
