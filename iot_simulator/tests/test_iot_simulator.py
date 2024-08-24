import pytest
from iot_simulator import IoTDevice

def test_iot_device():
    device = IoTDevice("test_device")
    data = device.get_data()
    
    assert "device_id" in data
    assert "timestamp" in data
    assert "temperature" in data
    assert "humidity" in data
    assert "pressure" in data
    
    assert data["device_id"] == "test_device"
    assert 0 <= data["temperature"] <= 100
    assert 0 <= data["humidity"] <= 100
    assert 900 <= data["pressure"] <= 1100

def test_kafka_producer(mocker):
    mock_producer = mocker.patch('kafka.KafkaProducer')
    mock_producer.return_value.send.return_value = None
    
    from iot_simulator import generate_data
    
    # Run generate_data for a short time
    mocker.patch('time.sleep', side_effect=InterruptedError)
    with pytest.raises(InterruptedError):
        generate_data(num_devices=1, interval=0)
    
    # Check if the producer was called
    mock_producer.return_value.send.assert_called()