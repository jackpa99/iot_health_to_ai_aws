# Kubernetes deployment (primary)

Portable K8s manifests. Tested patterns work on upstream K8s, OpenShift, EKS,
AKS, GKE, and on-prem distros (Rancher, Tanzu, etc.).

## One-time cluster prerequisites

The platform team installs these cluster-wide:

| Component | Purpose | Install |
|---|---|---|
| [Strimzi](https://strimzi.io/) | Manages Kafka CRs | `kubectl create -f 'https://strimzi.io/install/latest?namespace=iot' -n iot` |
| [External Secrets Operator](https://external-secrets.io/) | Materializes corp secrets (Vault / Key Vault / etc.) into K8s Secrets via OIDC | `helm install external-secrets external-secrets/external-secrets -n external-secrets --create-namespace` |

## Deploying the app

```bash
# 1. Edit deploy/k8s/secrets/secretstore.example.yaml — replace the `fake`
#    provider block with the real corp backend (Vault/Key Vault/…).
# 2. Edit deploy/k8s/configmap.yaml — set MODEL_STORAGE_URI and S3_ENDPOINT_URL
#    to your corp S3 endpoint.
# 3. Have CI set the image tags (or do it locally):
cd deploy/k8s
kustomize edit set image \
  REGISTRY/iot-health-to-ai/iot-simulator=harbor.corp.example.com/iot/iot-simulator:$(git rev-parse --short HEAD) \
  REGISTRY/iot-health-to-ai/spark-streaming=harbor.corp.example.com/iot/spark-streaming:$(git rev-parse --short HEAD) \
  REGISTRY/iot-health-to-ai/model-trainer=harbor.corp.example.com/iot/model-trainer:$(git rev-parse --short HEAD)

# 4. Apply
kubectl apply -k .
```

## What's deployed

| Workload | Type | Notes |
|---|---|---|
| Strimzi `Kafka` + `KafkaNodePool`s | CR | KRaft mode, 3 controllers / 3 brokers, persistent PVCs |
| `KafkaTopic` iot-data | CR | 12 partitions, 7-day retention |
| `ConfigMap` iot-config | — | Kafka bootstrap + MODEL_STORAGE_URI + S3 endpoint |
| `SecretStore` corp-secret-store | CR | Placeholder — replace with real backend |
| `ExternalSecret` model-store-creds | CR | S3 creds materialized for model-trainer |
| `Deployment` iot-simulator | — | Pushes synthetic telemetry to Kafka |
| `Deployment` spark-streaming | — | Consumes Kafka, runs anomaly detection |
| `CronJob` model-trainer | — | Nightly 02:17 retraining job |

## Cloud portability notes

- **Secrets**: the app reads `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` env
  vars — these are the standard names for *any* S3-compatible client (MinIO,
  Ceph RGW, Wasabi, corp S3), not an AWS-lock-in.
- **Object store**: swap `s3://` for `gs://`, `abfs://`, or `file://` in
  `MODEL_STORAGE_URI`; no code change required.
- **Registry**: the `REGISTRY/…` placeholders are rewritten by CI. Works with
  Harbor, Artifactory, Nexus, Quay, GHCR, ACR, GAR, ECR.
