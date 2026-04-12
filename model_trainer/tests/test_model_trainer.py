import os
import unittest
import tempfile
import pandas as pd
import numpy as np

# Point model storage at a temp directory for testing
_tmpdir = tempfile.mkdtemp()
os.environ["MODEL_STORAGE_URI"] = _tmpdir + "/"

from model_trainer import train_models
from model_trainer.model_storage import load_model, load_cohort_mapping
from model_trainer.cohort import compute_cohorts


class TestCohortComputation(unittest.TestCase):

    def setUp(self):
        devices = [f"us-east-1/d-{i:06d}" for i in range(50)]
        data = []
        for device in devices:
            device_data = pd.DataFrame({
                "device_id": [device] * 100,
                "temperature": np.random.uniform(20, 30, 100),
                "humidity": np.random.uniform(40, 60, 100),
                "pressure": np.random.uniform(990, 1010, 100)
            })
            data.append(device_data)
        self.df = pd.concat(data, ignore_index=True)

    def test_compute_cohorts(self):
        kmeans, mapping = compute_cohorts(self.df, n_cohorts=5)
        self.assertEqual(len(mapping), 50)
        cohort_ids = set(mapping.values())
        self.assertLessEqual(len(cohort_ids), 5)
        self.assertGreater(len(cohort_ids), 0)


class TestModelTrainer(unittest.TestCase):

    def setUp(self):
        devices = [f"us-east-1/d-{i:06d}" for i in range(20)]
        data = []
        for device in devices:
            device_data = pd.DataFrame({
                "device_id": [device] * 100,
                "temperature": np.random.uniform(20, 30, 100),
                "humidity": np.random.uniform(40, 60, 100),
                "pressure": np.random.uniform(990, 1010, 100)
            })
            data.append(device_data)
        self.df = pd.concat(data, ignore_index=True)

    def test_train_models_cohort_based(self):
        train_models(self.df, n_cohorts=3)

        # Verify cohort mapping was saved
        mapping = load_cohort_mapping()
        self.assertEqual(len(mapping), 20)

        # Verify models were saved for each cohort
        cohort_ids = set(mapping.values())
        for cohort_id in cohort_ids:
            anomaly_model = load_model("anomaly", cohort_id)
            self.assertEqual(
                str(type(anomaly_model)),
                "<class 'sklearn.ensemble._iforest.IsolationForest'>"
            )
            ace_model = load_model("ace", cohort_id)
            self.assertEqual(
                str(type(ace_model)),
                "<class 'sklearn.ensemble._forest.RandomForestClassifier'>"
            )

    def test_models_produce_predictions(self):
        train_models(self.df, n_cohorts=3)
        mapping = load_cohort_mapping()

        sample_cohort = list(set(mapping.values()))[0]
        model = load_model("anomaly", sample_cohort)

        X = self.df[["temperature", "humidity", "pressure"]].head(10)
        predictions = model.predict(X)
        self.assertEqual(len(predictions), 10)
        self.assertTrue(all((predictions == 1) | (predictions == -1)))


if __name__ == "__main__":
    unittest.main()
