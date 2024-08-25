# tests/test_iot_simulator.py
import unittest
from unittest.mock import patch, MagicMock
from iot_simulator import generate_device_data, simulate_iot_devices

class TestIoTSimulator(unittest.TestCase):

    def test_generate_device_data(self):
        device_id = 1
        data = generate_device_data(device_id)
        self.assertEqual(data['device_id'], device_id)
        self.assertIn('timestamp', data)
        self.assertIn('temperature', data)
        self.assertIn('humidity', data)
        self.assertIn('pressure', data)

    @patch('iot_simulator.KafkaProducer')
    @patch('iot_simulator.time.sleep', side_effect=InterruptedError)  # To break the infinite loop
    def test_simulate_iot_devices(self, mock_sleep, mock_kafka_producer):
        mock_producer = MagicMock()
        mock_kafka_producer.return_value = mock_producer

        num_devices = 3
        kafka_servers = ['localhost:9092']

        with self.assertRaises(InterruptedError):
            simulate_iot_devices(num_devices, kafka_servers)

        mock_kafka_producer.assert_called_once_with(
            bootstrap_servers=kafka_servers,
            value_serializer=unittest.mock.ANY
        )

        # Check that data was sent for each device
        self.assertEqual(mock_producer.send.call_count, num_devices)
        for i in range(num_devices):
            mock_producer.send.assert_any_call('iot-data', unittest.mock.ANY)

if __name__ == '__main__':
    unittest.main()