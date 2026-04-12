from __future__ import annotations

import json
import os
from typing import Any

from kafka import KafkaProducer


class KafkaMessageProducer:
    def __init__(self) -> None:
        self.broker: str = os.getenv("KAFKA_BROKER", "kafka:9092")
        self.topic: str = os.getenv("KAFKA_TOPIC", "iot-data")
        self.producer = KafkaProducer(
            bootstrap_servers=[self.broker],
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

    def send_message(self, message: dict[str, Any]) -> None:
        self.producer.send(self.topic, message)
        self.producer.flush()

    def close(self) -> None:
        self.producer.flush()
        self.producer.close()


if __name__ == "__main__":
    producer = KafkaMessageProducer()
    try:
        producer.send_message({"test": "message"})
    finally:
        producer.close()
