FROM python:3.12-slim-bookworm

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

ENV NAME=ModelTrainer
# MODEL_STORAGE_URI defaults to file:///tmp/models; override at deploy time
# (e.g. s3://bucket/prefix plus S3_ENDPOINT_URL for corp S3 / MinIO).
CMD ["python", "trainer.py"]
