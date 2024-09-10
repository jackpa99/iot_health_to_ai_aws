#!/bin/bash
set -e

echo "Starting IoT Simulator container at $(date)"

# Check if required environment variables are set
if [ -z "$KAFKA_BROKER" ]; then
  echo "Error: KAFKA_BROKER environment variable is not set"
  exit 1
fi

# Run the Python script
python iot_simulator.py || {
  echo "Error: IoT Simulator script failed to run"
  exit 1
}