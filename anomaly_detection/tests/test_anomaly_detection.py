import pytest
import numpy as np
from anomaly_detection import train_model, detect_anomalies

@pytest.fixture
def sample_data():
    np.random.seed(42)
    normal_data = np.random.normal(0, 1, (100, 3))
    anomalies = np.random.normal(5, 1, (10, 3))
    data = np.vstack((normal_data, anomalies))
    return data

def test_train_model(sample_data):
    model = train_model(sample_data)
    assert model is not None

def test_detect_anomalies(sample_data):
    model = train_model(sample_data)
    anomalies = detect_anomalies(model, sample_data)
    assert len(anomalies) > 0
    assert len(anomalies) < len(sample_data)

def test_load_data_from_s3(mocker):
    mock_s3 = mocker.patch('boto3.client')
    mock_s3.return_value.get_object.return_value = {
        'Body': mocker.MagicMock()
    }
    
    from anomaly_detection import load_data_from_s3
    
    data = load_data_from_s3()
    assert data is not None
    mock_s3.assert_called_once_with('s3')