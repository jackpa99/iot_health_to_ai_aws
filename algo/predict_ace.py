"""Predict ACE (Adverse Cardiac Event) from tabular patient data."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split


def load_data(filepath: str | Path) -> pd.DataFrame:
    return pd.read_csv(filepath)


def preprocess_data(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    features = data.drop("target", axis=1)
    labels = data["target"]
    return features, labels


def train_model(features: pd.DataFrame, labels: pd.Series):
    X_train, X_test, y_train, y_test = train_test_split(
        features, labels, test_size=0.2, random_state=42
    )
    model = RandomForestClassifier(random_state=42)
    model.fit(X_train, y_train)
    return model, X_test, y_test


def evaluate_model(model, X_test, y_test) -> None:
    predictions = model.predict(X_test)
    print(f"Accuracy: {accuracy_score(y_test, predictions):.4f}")
    print(classification_report(y_test, predictions))


if __name__ == "__main__":
    data = load_data("your_data_file.csv")
    features, labels = preprocess_data(data)
    model, X_test, y_test = train_model(features, labels)
    evaluate_model(model, X_test, y_test)
