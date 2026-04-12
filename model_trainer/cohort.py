import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

FEATURES = ["temperature", "humidity", "pressure"]


def compute_cohorts(df: pd.DataFrame, n_cohorts: int = 200):
    """Cluster devices into cohorts by their mean feature values.

    Parameters
    ----------
    df : DataFrame with columns [device_id, temperature, humidity, pressure, ...]
    n_cohorts : target number of cohorts (actual may be fewer if < n_cohorts devices)

    Returns
    -------
    kmeans_model : fitted KMeans
    mapping : dict  {device_id_str: cohort_id_str}
    """
    device_stats = df.groupby("device_id")[FEATURES].mean().reset_index()

    actual_k = min(n_cohorts, len(device_stats))
    kmeans = KMeans(n_clusters=actual_k, random_state=42, n_init=10)
    kmeans.fit(device_stats[FEATURES])

    device_stats["cohort_id"] = [str(label) for label in kmeans.labels_]
    mapping = dict(zip(device_stats["device_id"].astype(str), device_stats["cohort_id"]))
    return kmeans, mapping


def assign_cohort(device_means: dict, kmeans_model) -> str:
    """Assign a single device to a cohort given its aggregate feature means.

    Parameters
    ----------
    device_means : {"temperature": float, "humidity": float, "pressure": float}
    kmeans_model : fitted KMeans from compute_cohorts

    Returns
    -------
    cohort_id : str
    """
    X = np.array([[device_means[f] for f in FEATURES]])
    label = kmeans_model.predict(X)[0]
    return str(label)
