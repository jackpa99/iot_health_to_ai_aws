Telehealth is likely to continue booming in future. This application provides a lower cost alternative to premium services for remote vital signs mass monitoring and alerting, provided by healthcare providers.
Application integrates health and wellness metrics made available from fitness apps on mobile devices, uses AI based analysis to create personalised alerting per user, based on their own normal range of wellness. 
It could be enhanced to also provide AI chatbot that uses user's personal metrics history to discuss all things health and wellness related, personalised to the user.

![telehealth remote mass monitoring, alerting flowchart](flowchart-mvp.png)

Technical overview:
Mobile devices installed with fitness tracker (eg; Google Fit) have their data exposed on API endpoint or alternatively, customised, advanced IoT contactless device, sends data packets to AWS ecosystem (over MQTT protocol), containing a timestamp, device id and human vital signs.

Need to persist packets efficiently but data older than 6 months can be accessible after even 1 day wait.
Want AI model per user, to periodically, run AI model over user's historical data, with aim of learning to detect outliers in vital signs.


Diagram:
[IoT Devices] -> [IoT Core] or fitness tracker API endpoint -> [MSK (Kafka)] -> [S3]
                                                                                  |
                                                                  +-----------+---------------+---------------+----------------+----------------+
                                                                  v           v               v               v                v                v
                                                               [SageMaker] [S3 parquet]       [Athena]    [QuickSight]       [User UI]     [AI chatbot personalised on metrics (Rasa CALM) ]


==========

project_root/
│
├── iot_simulator/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── iot_simulator.py
│
│__ sagemaker training
│   ├── Dockerfile
│   ├── requirements.txt
│   └── anomaly_detection.py
│
├── anomaly_detection/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── anomaly_detection.py
│
└── .github/workflows
     │__ pipeline

==========

AWS IoT Core to MSK Setup

a. Create an MSK cluster:

Go to the Amazon MSK console
Create a new cluster with appropriate size and configuration
b. Create an IoT Rule:

Go to AWS IoT Core console
Create a new rule
Set the rule query statement to: SELECT * FROM 'iot/device/+'
Add an action to send data to Amazon MSK

========

Athena Query Setup
After the data is written to S3 as Parquet, set up Athena to query it:

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

To manually trigger metrics data simulation, for demo purposes:

python iot_simulator.py --devices 100 --duration 60


=====
CloudFormation template that sets up the majority of the AWS resources needed for this architecture. This template will create:

An S3 Bucket for Parquet data
An S3 Bucket for scripts
An ECS instance and hosted services
A SageMaker Notebook Instance
An Athena Workgroup
IAM Roles and Policies


May need to make some manual configurations in services like Athena and QuickSight.

=====
To use CloudFormation templates:

Go to the AWS CloudFormation console.
Click "Create stack" and choose "With new resources (standard)".
Upload the YAML file.

Review and create the stack.
After the stack is created:
Run github actions to trigger build
Configure Athena to use the created workgroup and set up your tables.
Set up QuickSight to connect to Athena fro console
Remember to delete the stack when done to avoid ongoing charges.
