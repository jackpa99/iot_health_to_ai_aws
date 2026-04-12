"""IoT device simulator that pushes telemetry to Kafka."""
from __future__ import annotations

import json
import logging
import os
import random
import sys
import time
from typing import Iterable

from kafka import KafkaProducer

LOG_DIR = os.getenv("IOT_LOG_DIR", "/var/log/iot-simulator")


def _configure_logging() -> logging.Logger:
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        handlers.append(logging.FileHandler(os.path.join(LOG_DIR, "app.log")))
    except OSError:
        # Log dir may be unwritable (e.g. in unit-test environments); stdout is enough.
        pass
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )
    return logging.getLogger("iot_simulator")


logger = _configure_logging()


def generate_device_data(device_id: int) -> dict:
    return {
        "device_id": device_id,
        "timestamp": int(time.time()),
        "temperature": random.uniform(20, 30),
        "humidity": random.uniform(40, 60),
        "pressure": random.uniform(990, 1010),
    }


def simulate_iot_devices(num_devices: int, kafka_bootstrap_servers: Iterable[str]) -> None:
    producer = KafkaProducer(
        bootstrap_servers=list(kafka_bootstrap_servers),
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    while True:
        for device_id in range(num_devices):
            data = generate_device_data(device_id)
            producer.send("iot-data", data)
            logger.info("Sent data for device_%s: %s", device_id, data)
        time.sleep(1)  # Send data every second


def main() -> None:
    try:
        logger.info("Starting IoT simulator...")
        num_devices = int(os.getenv("NUM_DEVICES", "10"))
        bootstrap = os.getenv("KAFKA_BROKER", "localhost:9092").split(",")
        simulate_iot_devices(num_devices, bootstrap)
    except Exception:
        logger.exception("IoT simulator crashed")
        sys.exit(1)


if __name__ == "__main__":
    main()
