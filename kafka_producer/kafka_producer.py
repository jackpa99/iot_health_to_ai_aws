# not actually required as iot_simulator has a producer
import os
from kafka import KafkaProducer
import json

class KafkaMessageProducer:
    def __init__(self):
        self.broker = os.getenv('KAFKA_BROKER', 'kafka:9092')
        self.topic = os.getenv('KAFKA_TOPIC', 'iot_data')
        self.producer = KafkaProducer(
            bootstrap_servers=[self.broker],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

    def send_message(self, message):
        self.producer.send(self.topic, message)
        self.producer.flush()

if __name__ == "__main__":
    producer = KafkaMessageProducer()
    # Example usage
    producer.send_message({"test": "message"})