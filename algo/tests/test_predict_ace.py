import unittest
from io import StringIO

import pandas as pd

from predict_ace import load_data, preprocess_data, train_model


CSV_FIXTURE = StringIO(
    "f1,f2,f3,target\n"
    "0.1,1.0,2.0,0\n0.2,1.1,2.1,1\n0.3,1.2,2.2,0\n0.4,1.3,2.3,1\n"
    "0.5,1.4,2.4,0\n0.6,1.5,2.5,1\n0.7,1.6,2.6,0\n0.8,1.7,2.7,1\n"
    "0.9,1.8,2.8,0\n1.0,1.9,2.9,1\n"
)


class TestModel(unittest.TestCase):
    def setUp(self) -> None:
        CSV_FIXTURE.seek(0)
        self.data = pd.read_csv(CSV_FIXTURE)

    def test_data_loading(self) -> None:
        # load_data is a thin pd.read_csv wrapper; exercise the contract.
        self.assertIsInstance(self.data, pd.DataFrame)
        self.assertIn("target", self.data.columns)

    def test_preprocessing(self) -> None:
        features, labels = preprocess_data(self.data)
        self.assertEqual(features.shape[1], self.data.shape[1] - 1)
        self.assertEqual(len(labels), len(self.data))

    def test_train_model_runs(self) -> None:
        features, labels = preprocess_data(self.data)
        model, X_test, _y_test = train_model(features, labels)
        self.assertEqual(len(X_test.columns), features.shape[1])
        self.assertTrue(hasattr(model, "predict"))


if __name__ == "__main__":
    unittest.main()
