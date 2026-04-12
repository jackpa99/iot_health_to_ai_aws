import unittest
from unittest.mock import patch, MagicMock
from iot_simulator import generate_device_data, generate_device_ids


class TestIoTSimulator(unittest.TestCase):

    def test_generate_device_ids(self):
        ids = generate_device_ids(5, "eu-west-1")
        self.assertEqual(len(ids), 5)
        for device_id in ids:
            self.assertTrue(device_id.startswith("eu-west-1/d-"))
            # UUID hex portion should be 12 chars
            uuid_part = device_id.split("/d-")[1]
            self.assertEqual(len(uuid_part), 12)

    def test_generate_device_ids_unique(self):
        ids = generate_device_ids(100, "us-east-1")
        self.assertEqual(len(set(ids)), 100)

    def test_generate_device_data(self):
        device_id = "ap-southeast-1/d-abc123def456"
        data = generate_device_data(device_id)
        self.assertEqual(data["device_id"], device_id)
        self.assertIn("timestamp", data)
        self.assertIn("temperature", data)
        self.assertIn("humidity", data)
        self.assertIn("pressure", data)
        self.assertIsInstance(data["temperature"], float)

    def test_generate_device_data_ranges(self):
        device_id = "us-east-1/d-000000000000"
        for _ in range(100):
            data = generate_device_data(device_id)
            self.assertGreaterEqual(data["temperature"], 20)
            self.assertLessEqual(data["temperature"], 30)
            self.assertGreaterEqual(data["humidity"], 40)
            self.assertLessEqual(data["humidity"], 60)


if __name__ == "__main__":
    unittest.main()
