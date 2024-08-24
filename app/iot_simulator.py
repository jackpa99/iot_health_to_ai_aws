import boto3
import json
import random
import time
from datetime import datetime
import argparse

# Initialize AWS IoT Core client
iot_client = boto3.client('iot-data', region_name='us-west-2')

def generate_vital_signs(device_id, timestamp):
    """Generate random vital signs with occasional outliers."""
    heart_rate = random.gauss(75, 10)
    blood_pressure_systolic = random.gauss(120, 10)
    blood_pressure_diastolic = random.gauss(80, 8)
    temperature = random.gauss(98.6, 0.6)
    
    # Introduce occasional outliers
    if random.random() < 0.05:  # 5% chance of outlier
        heart_rate += random.choice([-30, 30])
        temperature += random.choice([-2, 2])

    return {
        "device_id": device_id,
        "timestamp": timestamp,
        "heart_rate": round(heart_rate, 1),
        "blood_pressure": f"{round(blood_pressure_systolic)}/{round(blood_pressure_diastolic)}",
        "temperature": round(temperature, 1)
    }

def publish_message(topic, message):
    """Publish message to AWS IoT Core."""
    iot_client.publish(
        topic=topic,
        qos=1,
        payload=json.dumps(message)
    )

def simulate_devices(num_devices, duration_minutes):
    """Simulate multiple IoT devices sending data."""
    end_time = time.time() + (duration_minutes * 60)
    while time.time() < end_time:
        timestamp = datetime.utcnow().isoformat()
        for device_id in range(1, num_devices + 1):
            data = generate_vital_signs(f"device_{device_id}", timestamp)
            publish_message(f"iot/device/{device_id}", data)
        time.sleep(1)  # Wait for 1 second before next batch

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IoT Device Simulator")
    parser.add_argument("--devices", type=int, default=10, help="Number of devices to simulate")
    parser.add_argument("--duration", type=int, default=5, help="Duration in minutes")
    args = parser.parse_args()

    print(f"Simulating {args.devices} devices for {args.duration} minutes...")
    simulate_devices(args.devices, args.duration)
    print("Simulation complete.")
