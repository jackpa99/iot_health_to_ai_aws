IoT devices, large number, needs to send small data packets to AWS ecosystem, containing a field suitable for time series along with other fields for human vital signs and a field representing each unique device.
Latency is not critical and few lost packets is permissible.
Need to persist packets efficiently but data older than 6 months can be accessible after even 1 day wait.
Want AI model to periodically or on demand, run AI model with aim of learning to detect outliers in vital signs.




Diagram:
[IoT Devices] -> [IoT Core] -> [MSK (Kafka)] -> [Spark on EMR] -> [S3 (Parquet Data)]
                                                    |
                                    +---------------+---------------+
                                    v               v               v
                                [Athena]       [SageMaker]    [QuickSight]

[Step Functions] (for orchestrating SageMaker jobs and Spark jobs)

==========

project_root/
│
├── iot_simulator/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── iot_simulator.py
│
├── kafka_producer/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── kafka_producer.py
│
├── spark_streaming/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── spark_streaming.py
│
├── anomaly_detection/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── anomaly_detection.py
│
├── docker-compose.yml
└── .env

==========

AWS IoT Core to MSK Setup
For this setup, you'll need to use the AWS Management Console or AWS CLI:

a. Create an MSK cluster:

Go to the Amazon MSK console
Create a new cluster with appropriate size and configuration
b. Create an IoT Rule:

Go to AWS IoT Core console
Create a new rule
Set the rule query statement to: SELECT * FROM 'iot/device/+'
Add an action to send data to Amazon MSK

========

Spark on EMR Job
Create an EMR cluster and use the following PySpark script to process data from Kafka and write to S3 as Parquet:

=====

Athena Query Setup
After the data is written to S3 as Parquet, you can set up Athena to query it:

a. Create an Athena table:

CREATE EXTERNAL TABLE iot_data (
  device_id STRING,
  timestamp STRING,
  heart_rate DOUBLE,
  blood_pressure STRING,
  temperature DOUBLE
)
PARTITIONED BY (device_id STRING)
STORED AS PARQUET
LOCATION 's3://your-bucket-parquet-data/';

MSCK REPAIR TABLE iot_data;

=====
 Query the data:

SELECT * FROM iot_data
WHERE device_id = 'device_1'
LIMIT 10;

======

SageMaker Integration
Here's a basic script to train a model using SageMaker:

# sagemaker_train.py

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

========

Step Functions for Orchestration
Create a Step Functions state machine to orchestrate the EMR job and SageMaker training:

{
  "Comment": "IoT Data Processing and Model Training",
  "StartAt": "Start EMR Job",
  "States": {
    "Start EMR Job": {
      "Type": "Task",
      "Resource": "arn:aws:states:::elasticmapreduce:addStep.sync",
      "Parameters": {
        "ClusterId": "YOUR_EMR_CLUSTER_ID",
        "Step": {
          "Name": "Spark Streaming Job",
          "ActionOnFailure": "CONTINUE",
          "HadoopJarStep": {
            "Jar": "command-runner.jar",
            "Args": [
              "spark-submit",
              "--deploy-mode",
              "cluster",
              "s3://your-bucket-scripts/emr_spark_job.py"
            ]
          }
        }
      },
      "Next": "Train SageMaker Model"
    },
    "Train SageMaker Model": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sagemaker:createTrainingJob.sync",
      "Parameters": {
        "TrainingJobName": "IoT-Anomaly-Detection-Job",
        "AlgorithmSpecification": {
          "TrainingImage": "YOUR_SAGEMAKER_TRAINING_IMAGE",
          "TrainingInputMode": "File"
        },
        "RoleArn": "YOUR_SAGEMAKER_ROLE_ARN",
        "InputDataConfig": [
          {
            "ChannelName": "train",
            "DataSource": {
              "S3DataSource": {
                "S3DataType": "S3Prefix",
                "S3Uri": "s3://your-bucket-parquet-data/"
              }
            }
          }
        ],
        "OutputDataConfig": {
          "S3OutputPath": "s3://your-bucket-model-output/"
        },
        "ResourceConfig": {
          "InstanceCount": 1,
          "InstanceType": "ml.m5.xlarge",
          "VolumeSizeInGB": 30
        },
        "StoppingCondition": {
          "MaxRuntimeInSeconds": 86400
        }
      },
      "End": true
    }
  }
}

========
To manually trigger this pipeline:

Save the IoT simulator script and run it with desired parameters:

python iot_simulator.py --devices 100 --duration 60

The data will flow through IoT Core to MSK, then be processed by the Spark job on EMR and stored in S3.
You can manually start the Step Functions state machine to process the data and train a model, or set up a CloudWatch event to trigger it periodically.
This implementation provides a complete pipeline for ingesting IoT data, processing it with Spark, storing it as Parquet in S3, and using it for analytics (Athena) and machine learning (SageMaker). The Step Functions workflow allows for orchestration of the entire process.

Remember to replace placeholder values (like YOUR_MSK_BROKERS, YOUR_EMR_CLUSTER_ID, etc.) with your actual AWS resource identifiers. Also, ensure that all necessary IAM permissions are set up for the various services to interact with each other.

=====
CloudFormation template that sets up the majority of the AWS resources needed for this architecture. This template will create:

An IoT Core Rule
An MSK Cluster
An S3 Bucket for Parquet data
An S3 Bucket for scripts and checkpoints
An EMR Cluster
A SageMaker Notebook Instance
An Athena Workgroup
IAM Roles and Policies
A Step Functions State Machine

Please note that you'll need to manually upload your scripts to the S3 bucket after creation, and you may need to make some manual configurations in services like Athena and QuickSight.

AWSTemplateFormatVersion: '2010-09-09'
Description: 'CloudFormation template for IoT data processing with Kafka and Spark'

Parameters:
  KafkaClientSubnets:
    Type: List<AWS::EC2::Subnet::Id>
    Description: Subnets for Kafka clients

Resources:
  # S3 Buckets
  ParquetDataBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub '${AWS::StackName}-parquet-data'

  ScriptsAndCheckpointsBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub '${AWS::StackName}-scripts-and-checkpoints'

  # IoT Core Rule
  IoTRule:
    Type: AWS::IoT::TopicRule
    Properties:
      RuleName: !Sub '${AWS::StackName}-to-msk-rule'
      TopicRulePayload:
        SQL: "SELECT * FROM 'iot/device/+'"
        Actions:
          - Kafka:
              DestinationArn: !GetAtt MSKCluster.Arn
              Topic: 'iot-data'
              ClientProperties:
                BootstrapServers: !GetAtt MSKCluster.BootstrapBrokers

  # MSK Cluster
  MSKCluster:
    Type: AWS::MSK::Cluster
    Properties:
      ClusterName: !Sub '${AWS::StackName}-msk-cluster'
      KafkaVersion: '2.8.1'
      NumberOfBrokerNodes: 3
      BrokerNodeGroupInfo:
        InstanceType: kafka.t3.small
        ClientSubnets: !Ref KafkaClientSubnets
        StorageInfo:
          EBSStorageInfo:
            VolumeSize: 100

  # EMR Cluster
  EMRCluster:
    Type: AWS::EMR::Cluster
    Properties:
      Name: !Sub '${AWS::StackName}-emr-cluster'
      ReleaseLabel: 'emr-6.5.0'
      Applications:
        - Name: Spark
        - Name: Hadoop
      Instances:
        MasterInstanceGroup:
          InstanceCount: 1
          InstanceType: m5.xlarge
        CoreInstanceGroup:
          InstanceCount: 2
          InstanceType: m5.xlarge
        Ec2SubnetId: !Select [0, !Ref KafkaClientSubnets]
      JobFlowRole: !Ref EMRInstanceProfile
      ServiceRole: !Ref EMRServiceRole

  # SageMaker Notebook Instance
  SageMakerNotebookInstance:
    Type: AWS::SageMaker::NotebookInstance
    Properties:
      InstanceType: 'ml.t3.medium'
      RoleArn: !GetAtt SageMakerRole.Arn
      NotebookInstanceName: !Sub '${AWS::StackName}-notebook'

  # Athena Workgroup
  AthenaWorkgroup:
    Type: AWS::Athena::WorkGroup
    Properties:
      Name: !Sub '${AWS::StackName}-workgroup'
      Description: 'Workgroup for querying IoT data'
      State: ENABLED
      WorkGroupConfiguration:
        ResultConfiguration:
          OutputLocation: !Sub 's3://${ParquetDataBucket}/athena-results/'

  # IAM Roles
  EMRServiceRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: elasticmapreduce.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AmazonElasticMapReduceRole

  EMRInstanceProfile:
    Type: AWS::IAM::InstanceProfile
    Properties:
      Roles:
        - !Ref EMRInstanceRole

  EMRInstanceRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: ec2.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AmazonElasticMapReduceforEC2Role
      Policies:
        - PolicyName: S3Access
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - s3:GetObject
                  - s3:PutObject
                Resource:
                  - !Sub 'arn:aws:s3:::${ParquetDataBucket}/*'
                  - !Sub 'arn:aws:s3:::${ScriptsAndCheckpointsBucket}/*'

  SageMakerRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: sagemaker.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/AmazonSageMakerFullAccess
      Policies:
        - PolicyName: S3Access
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - s3:GetObject
                  - s3:PutObject
                Resource:
                  - !Sub 'arn:aws:s3:::${ParquetDataBucket}/*'
                  - !Sub 'arn:aws:s3:::${ScriptsAndCheckpointsBucket}/*'

  # Step Functions State Machine
  StepFunctionsStateMachine:
    Type: AWS::StepFunctions::StateMachine
    Properties:
      RoleArn: !GetAtt StepFunctionsRole.Arn
      DefinitionString: !Sub 
        - |-
          {
            "Comment": "IoT Data Processing and Model Training",
            "StartAt": "Start EMR Job",
            "States": {
              "Start EMR Job": {
                "Type": "Task",
                "Resource": "arn:aws:states:::elasticmapreduce:addStep.sync",
                "Parameters": {
                  "ClusterId": "${EMRClusterId}",
                  "Step": {
                    "Name": "Spark Streaming Job",
                    "ActionOnFailure": "CONTINUE",
                    "HadoopJarStep": {
                      "Jar": "command-runner.jar",
                      "Args": [
                        "spark-submit",
                        "--deploy-mode",
                        "cluster",
                        "s3://${ScriptsBucket}/emr_spark_job.py"
                      ]
                    }
                  }
                },
                "Next": "Train SageMaker Model"
              },
              "Train SageMaker Model": {
                "Type": "Task",
                "Resource": "arn:aws:states:::sagemaker:createTrainingJob.sync",
                "Parameters": {
                  "TrainingJobName": "IoT-Anomaly-Detection-Job",
                  "AlgorithmSpecification": {
                    "TrainingImage": "${SageMakerTrainingImage}",
                    "TrainingInputMode": "File"
                  },
                  "RoleArn": "${SageMakerRoleArn}",
                  "InputDataConfig": [
                    {
                      "ChannelName": "train",
                      "DataSource": {
                        "S3DataSource": {
                          "S3DataType": "S3Prefix",
                          "S3Uri": "s3://${ParquetBucket}/"
                        }
                      }
                    }
                  ],
                  "OutputDataConfig": {
                    "S3OutputPath": "s3://${ParquetBucket}/model-output/"
                  },
                  "ResourceConfig": {
                    "InstanceCount": 1,
                    "InstanceType": "ml.m5.xlarge",
                    "VolumeSizeInGB": 30
                  },
                  "StoppingCondition": {
                    "MaxRuntimeInSeconds": 86400
                  }
                },
                "End": true
              }
            }
          }
        - EMRClusterId: !Ref EMRCluster
          ScriptsBucket: !Ref ScriptsAndCheckpointsBucket
          SageMakerTrainingImage: !Sub '${AWS::AccountId}.dkr.ecr.${AWS::Region}.amazonaws.com/sagemaker-scikit-learn:0.23-1-cpu-py3'
          SageMakerRoleArn: !GetAtt SageMakerRole.Arn
          ParquetBucket: !Ref ParquetDataBucket

  StepFunctionsRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: states.amazonaws.com
            Action: sts:AssumeRole
      Policies:
        - PolicyName: StepFunctionsAccess
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - elasticmapreduce:AddJobFlowSteps
                  - elasticmapreduce:DescribeStep
                  - elasticmapreduce:CancelSteps
                Resource: '*'
              - Effect: Allow
                Action:
                  - sagemaker:CreateTrainingJob
                  - sagemaker:DescribeTrainingJob
                  - sagemaker:StopTrainingJob
                Resource: '*'
              - Effect: Allow
                Action:
                  - iam:PassRole
                Resource:
                  - !GetAtt EMRServiceRole.Arn
                  - !GetAtt SageMakerRole.Arn

Outputs:
  ParquetDataBucketName:
    Description: 'Name of the S3 bucket for Parquet data'
    Value: !Ref ParquetDataBucket
  ScriptsAndCheckpointsBucketName:
    Description: 'Name of the S3 bucket for scripts and checkpoints'
    Value: !Ref ScriptsAndCheckpointsBucket
  MSKClusterArn:
    Description: 'ARN of the MSK Cluster'
    Value: !GetAtt MSKCluster.Arn
  EMRClusterId:
    Description: 'ID of the EMR Cluster'
    Value: !Ref EMRCluster
  SageMakerNotebookInstanceName:
    Description: 'Name of the SageMaker Notebook Instance'
    Value: !Ref SageMakerNotebookInstance
  AthenaWorkgroupName:
    Description: 'Name of the Athena Workgroup'
    Value: !Ref AthenaWorkgroup
  StepFunctionsStateMachineArn:
    Description: 'ARN of the Step Functions State Machine'
    Value: !Ref StepFunctionsStateMachine

=====
To use this CloudFormation template:

Save it as a YAML file (e.g., iot-kafka-spark-setup.yaml).
Go to the AWS CloudFormation console.
Click "Create stack" and choose "With new resources (standard)".
Upload the YAML file.
Fill in the required parameter (KafkaClientSubnets).

Review and create the stack.
After the stack is created:

Upload your scripts (e.g., emr_spark_job.py) to the ScriptsAndCheckpointsBucket.
Configure Athena to use the created workgroup and set up your tables.
Set up QuickSight to connect to Athena (this needs to be done manually).
You may need to adjust security groups to allow proper communication between services.
Remember to delete the stack when you're done to avoid ongoing charges, and be aware that running these services will incur costs in your AWS account.

