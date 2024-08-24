import boto3
import sagemaker
from sagemaker import get_execution_role
from sagemaker.sklearn.estimator import SKLearn

role = get_execution_role()
sagemaker_session = sagemaker.Session()

# Set up the SKLearn estimator
sklearn = SKLearn(
    entry_point='train.py',
    role=role,
    instance_count=1,
    instance_type='ml.m5.xlarge',
    framework_version='0.23-1',
    base_job_name='iot-anomaly-detection',
    sagemaker_session=sagemaker_session
)

# Start the training job
sklearn.fit({'train': 's3://your-bucket-parquet-data/'})
