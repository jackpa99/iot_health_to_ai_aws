# sagemaker_train.py
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import IsolationForest
import joblib

# Simulating data preparation for multiple devices
devices = range(10)
data = []
for device in devices:
    device_data = pd.DataFrame({
        'device_id': [device] * 1000,
        'temperature': np.random.uniform(20, 30, 1000),
        'humidity': np.random.uniform(40, 60, 1000),
        'pressure': np.random.uniform(990, 1010, 1000)
    })
    data.append(device_data)

df = pd.concat(data, ignore_index=True)

# Train a separate model for each device
for device in devices:
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