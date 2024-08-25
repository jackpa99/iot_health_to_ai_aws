# tests/test_sagemaker_train.py
import unittest
import pandas as pd
import numpy as np
import joblib
import os
from sagemaker_train import train_models

class TestSageMakerTrain(unittest.TestCase):

    def setUp(self):
        # Create a sample dataset
        devices = range(2)
        data = []
        for device in devices:
            device_data = pd.DataFrame({
                'device_id': [device] * 100,
                'temperature': np.random.uniform(20, 30, 100),
                'humidity': np.random.uniform(40, 60, 100),
                'pressure': np.random.uniform(990, 1010, 100)
            })
            data.append(device_data)
        self.df = pd.concat(data, ignore_index=True)

    def test_train_models(self):
        # Train models
        train_models(self.df)

        # Check if models are saved for each device
        for device in range(2):
            model_path = f'/tmp/model_device_{device}.joblib'
            self.assertTrue(os.path.exists(model_path))

            # Load the model and make sure it's an IsolationForest
            model = joblib.load(model_path)
            self.assertEqual(str(type(model)), "<class 'sklearn.ensemble._iforest.IsolationForest'>")

            # Test the model with some data
            device_data = self.df[self.df['device_id'] == device]
            features = ['temperature', 'humidity', 'pressure']
            X = device_data[features]
            predictions = model.predict(X)

            # Check if predictions are made for all rows
            self.assertEqual(len(predictions), len(X))

            # Check if predictions are either 1 (normal) or -1 (anomaly)
            self.assertTrue(all((predictions == 1) | (predictions == -1)))

    def tearDown(self):
        # Clean up saved models
        for device in range(2):
            model_path = f'/tmp/model_device_{device}.joblib'
            if os.path.exists(model_path):
                os.remove(model_path)

if __name__ == '__main__':
    unittest.main()