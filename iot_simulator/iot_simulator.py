import os
from kafka import KafkaProducer
import json
import time
import random

# Use environment variables for configuration
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'kafka:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'iot_data')

# Initialize Kafka producer
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

class IoTDevice:
    # ... (rest of the class remains the same)

    def generate_data(num_devices=10, interval=1):
        devices = [IoTDevice(f"device_{i}") for i in range(num_devices)]
    
    while True:
        for device in devices:
            data = device.get_data()
            producer.send(KAFKA_TOPIC, data)
        time.sleep(interval)

if __name__ == "__main__":
    generate_data()