# IoT simulator does the following:

#It simulates multiple devices (10 in this case, but you can adjust the NUM_DEVICES constant).
#Each device has a unique device_id.
#The generate_device_data function creates data for a single device, including a device ID and timestamp.
#The simulate_iot_devices function continuously generates data for all devices and sends it to Kafka.

import random
import sys
import time
import json
from kafka import KafkaProducer
import logging

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/var/log/iot-simulator/app.log')
    ]
)

logger = logging.getLogger('iot_simulator')

def generate_device_data(device_id):
    return {
        "device_id": device_id,
        "timestamp": int(time.time()),
        "temperature": random.uniform(20, 30),
        "humidity": random.uniform(40, 60),
        "pressure": random.uniform(990, 1010)
    }

def simulate_iot_devices(num_devices, kafka_bootstrap_servers):
    producer = KafkaProducer(
        bootstrap_servers=kafka_bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    while True:
        for device_id in range(num_devices):
            data = generate_device_data(device_id)
            producer.send('iot-data', data)
            print(f"Sent data for device {device_id}: {data}")
            logging.info(f"Sent data for device_{device_id}: {data}")
        time.sleep(1)  # Send data every second

def main():
    try:
        logger.info("Starting IoT simulator...")
        NUM_DEVICES = 10  # Simulate 10 IoT devices
        KAFKA_BOOTSTRAP_SERVERS = ['localhost:9092']  # Update with Kafka server(s)
    
        simulate_iot_devices(NUM_DEVICES, KAFKA_BOOTSTRAP_SERVERS)
    except Exception as e:
        logger.exception(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
    