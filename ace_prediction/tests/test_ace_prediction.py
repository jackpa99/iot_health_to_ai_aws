import os
import sys
import unittest
import tempfile
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

# Point model storage at a temp directory for testing
_tmpdir = tempfile.mkdtemp()
os.environ["MODEL_STORAGE_URI"] = _tmpdir + "/"

# Add model_trainer dir so model_storage is importable
_base = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, _base)
sys.path.insert(0, os.path.join(_base, "..", "model_trainer"))

from model_storage import save_model, save_cohort_mapping
from ace_prediction.ace_prediction import _get_ace_model, _get_cohort_mapping, refresh_ace_models


class TestACEPrediction(unittest.TestCase):

    def _train_and_save_dummy_model(self, cohort_id: str):
        X = np.array([[25, 50, 1000], [26, 51, 1001], [30, 60, 1010], [20, 40, 990]])
        y = np.array([0, 0, 1, 1])
        model = RandomForestClassifier(random_state=42)
        model.fit(X, y)
        save_model(model, "ace", cohort_id)
        return model

    def test_cohort_model_lookup(self):
        """Model loaded via cohort_id after mapping lookup."""
        self._train_and_save_dummy_model(cohort_id="42")
        save_cohort_mapping({"us-east-1/d-aaa001": "42", "us-east-1/d-aaa002": "42"})
        refresh_ace_models()

        mapping = _get_cohort_mapping()
        cohort_id = mapping.get("us-east-1/d-aaa001")
        self.assertEqual(cohort_id, "42")

        model = _get_ace_model(cohort_id)
        self.assertIsNotNone(model)

        proba = model.predict_proba(np.array([[25, 50, 1000]]))
        self.assertEqual(proba.shape[1], 2)

    def test_no_model_returns_none(self):
        """Unknown cohort returns None gracefully."""
        refresh_ace_models()
        result = _get_ace_model("nonexistent_cohort")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
