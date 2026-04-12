import os
import unittest
from pathlib import Path

import fsspec
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from trainer import train_models


class TestTrainer(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = Path(os.environ.get("PYTEST_TMPDIR", "/tmp")) / "trainer_test_models"
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        # Exercise the fsspec code path on the local filesystem; s3:// swaps in
        # at deploy time via the MODEL_STORAGE_URI env var.
        self.storage_uri = f"file://{self.tmp_dir}"
        rng = np.random.default_rng(42)
        frames = [
            pd.DataFrame(
                {
                    "device_id": [device] * 100,
                    "temperature": rng.uniform(20, 30, 100),
                    "humidity": rng.uniform(40, 60, 100),
                    "pressure": rng.uniform(990, 1010, 100),
                }
            )
            for device in range(2)
        ]
        self.df = pd.concat(frames, ignore_index=True)

    def test_train_models(self) -> None:
        paths = train_models(self.df, storage_uri=self.storage_uri)
        self.assertEqual(len(paths), 2)
        for device in range(2):
            path = self.tmp_dir / f"model_device_{device}.joblib"
            self.assertTrue(path.exists())

            # Round-trip through fsspec to validate the abstraction, not just the
            # local write path.
            with fsspec.open(f"file://{path}", "rb") as fh:
                model = joblib.load(fh)
            self.assertIsInstance(model, IsolationForest)

            X = self.df[self.df["device_id"] == device][["temperature", "humidity", "pressure"]]
            preds = model.predict(X)
            self.assertEqual(len(preds), len(X))
            self.assertTrue(np.isin(preds, (-1, 1)).all())

    def tearDown(self) -> None:
        for device in range(2):
            path = self.tmp_dir / f"model_device_{device}.joblib"
            if path.exists():
                path.unlink()


if __name__ == "__main__":
    unittest.main()
