import pytest
from unittest.mock import patch, MagicMock
import sagemaker_train

@pytest.fixture
def mock_sagemaker():
    with patch('sagemaker.Session') as mock_session, \
         patch('sagemaker.estimator.Estimator') as mock_estimator:
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_estimator_instance = MagicMock()
        mock_estimator.return_value = mock_estimator_instance
        yield mock_session_instance, mock_estimator_instance

def test_train_model(mock_sagemaker):
    mock_session, mock_estimator = mock_sagemaker
    
    # Mock the necessary methods and attributes
    mock_session.default_bucket.return_value = 'test-bucket'
    mock_estimator.latest_training_job.job_name = 'test-job'
    mock_estimator.model_data = 's3://test-bucket/test-job/output/model.tar.gz'

    # Call the function we want to test
    model_uri = sagemaker_train.train_model()

    # Assert that the necessary methods were called
    mock_session.default_bucket.assert_called_once()
    mock_estimator.fit.assert_called_once()

    # Assert that the function returns the correct model URI
    assert model_uri == 's3://test-bucket/test-job/output/model.tar.gz'

def test_prepare_data():
    # You would implement this test based on how prepare_data is implemented
    # For example:
    data = sagemaker_train.prepare_data()
    assert isinstance(data, dict)
    assert 'train' in data
    assert 'validation' in data

def test_create_estimator(mock_sagemaker):
    mock_session, _ = mock_sagemaker
    
    estimator = sagemaker_train.create_estimator(mock_session)
    
    # Assert that the Estimator was created with the correct parameters
    # The exact assertions will depend on how you've implemented create_estimator
    assert estimator is not None

# Add more tests as needed for other functions in sagemaker_train.py