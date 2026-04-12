import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import IsolationForest
import joblib
from kafka import KafkaConsumer
import json

# Kafka consumer setup
KAFKA_TOPIC = 'iot-data'
KAFKA_BOOTSTRAP_SERVERS = ['localhost:9092']  # Update with your Kafka server(s)

consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='sagemaker_training_group'
)

# Initialize a DataFrame to store consumed data
data = []

# Consume data from Kafka
for message in consumer:
    data.append(message.value)

    # Optional: Limit data consumption to a certain number of records for training
    if len(data) >= 10000:  # Change this limit as needed
        break

# Convert to DataFrame
df = pd.DataFrame(data)

# Train a separate model for each device
device_ids = df['device_id'].unique()
for device in device_ids:
    device_df = df[df['device_id'] == device]
    features = ['temperature', 'humidity', 'pressure']
    X = device_df[features]
    
    train, test = train_test_split(X, test_size=0.2)

    # Train model
    model = IsolationForest(contamination=0.1, random_state=42)
    model.fit(train)

    # Save model
    joblib.dump(model, f'/tmp/model_device_{device}.joblib')

print("Training complete. Models saved for each device.")