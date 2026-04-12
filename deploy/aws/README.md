# AWS deployment (reference only)

These templates target AWS ECS/ECR/CloudFormation and are retained as historical
reference. They are **not** the primary deployment path — see `deploy/k8s/` for
the portable K8s manifests used in corp cloud.

## Files

| File | Purpose |
|---|---|
| `iot-kafka-spark-setup.yaml` | CloudFormation: VPC, EC2, S3 bucket, SageMaker IAM role |
| `iot-ecr-ecs-cloudf.yaml` | CloudFormation: ECR repo, ECS cluster |
| `ecs-task-execution-role-template.yml` | CloudFormation: IAM roles for ECS task execution |
| `task-definition-template.json` | ECS task definition template |
| `pipeline.yaml` | GitHub Actions workflow fragment for ECR push + ECS deploy |

## Using these

Deploying with these files requires:
- An AWS account with permissions to create the resources above.
- The corresponding `.github/workflows/deploy-aws.yml` workflow, invoked via
  `workflow_dispatch` (it is no longer auto-triggered on `push`).
- AWS-scoped GitHub secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_AC`.

## If you are migrating off AWS

- The application code **does not** use `boto3` or the SageMaker SDK — they
  were only ever listed in `requirements.txt` and are now removed.
- Model artifacts are written via `fsspec`, so the same trainer binary writes
  to `s3://` on AWS, `abfs://` on Azure, `gs://` on GCP, or `file://` on a PVC
  simply by changing `MODEL_STORAGE_URI`.
- Kafka is vendor-neutral; Strimzi manifests in `deploy/k8s/kafka/` replace the
  EC2-hosted broker in `iot-kafka-spark-setup.yaml`.
