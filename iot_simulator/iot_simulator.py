import random
import sys
import time
import json
import os
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from kafka import KafkaProducer

logger = logging.getLogger("iot_simulator")


def generate_device_ids(num_devices: int, region: str) -> list[str]:
    """Generate region-prefixed UUID device IDs."""
    return [f"{region}/d-{uuid.uuid4().hex[:12]}" for _ in range(num_devices)]


def generate_device_data(device_id: str):
    return {
        "device_id": device_id,
        "timestamp": int(time.time()),
        "temperature": random.uniform(20, 30),
        "humidity": random.uniform(40, 60),
        "pressure": random.uniform(990, 1010)
    }


def simulate_device_batch(producer, device_ids: list[str], topic: str,
                          offline_probability: float = 0.02):
    """Simulate a batch of devices, including intermittent connectivity.

    Each call simulates one tick for all devices in the batch.
    Devices with offline_probability chance go offline and buffer messages,
    then send a burst on reconnect.
    """
    buffers: dict[str, list[dict]] = {}

    while True:
        for device_id in device_ids:
            data = generate_device_data(device_id)

            if random.random() < offline_probability:
                # Device goes offline — buffer messages
                if device_id not in buffers:
                    buffers[device_id] = []
                buffers[device_id].append(data)
                continue

            # Device is online — send current data
            producer.send(topic, key=device_id.encode(), value=data)

            # If device was offline, flush buffered messages (stale timestamps)
            if device_id in buffers:
                for buffered in buffers.pop(device_id):
                    producer.send(topic, key=device_id.encode(), value=buffered)

        time.sleep(1)


def simulate_iot_devices(num_devices: int, kafka_bootstrap_servers: list[str],
                         region: str, num_threads: int, topic: str):
    """Simulate devices using a thread pool for throughput."""
    producer = KafkaProducer(
        bootstrap_servers=kafka_bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=None,  # key is already bytes
        linger_ms=50,
        batch_size=65536,
        compression_type="lz4",
    )

    device_ids = generate_device_ids(num_devices, region)
    logger.info("Generated %d device IDs in region %s", num_devices, region)

    # Split devices across threads
    chunk_size = max(1, len(device_ids) // num_threads)
    chunks = [device_ids[i:i + chunk_size] for i in range(0, len(device_ids), chunk_size)]

    logger.info("Distributing across %d threads (%d devices/thread)",
                len(chunks), chunk_size)

    with ThreadPoolExecutor(max_workers=len(chunks)) as executor:
        futures = [
            executor.submit(simulate_device_batch, producer, chunk, topic)
            for chunk in chunks
        ]
        # Block until interrupted
        for f in futures:
            f.result()


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    try:
        logger.info("Starting IoT simulator...")
        NUM_DEVICES = int(os.getenv("NUM_DEVICES", "1000"))
        NUM_THREADS = int(os.getenv("NUM_THREADS", "4"))
        REGION = os.getenv("REGION", "us-east-1")
        KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
        TOPIC = os.getenv("KAFKA_TOPIC", "iot-data")

        simulate_iot_devices(NUM_DEVICES, [KAFKA_BROKER], REGION, NUM_THREADS, TOPIC)
    except Exception as e:
        logger.exception("An error occurred: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
