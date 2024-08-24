import pytest
from kafka_producer import KafkaMessageProducer

def test_kafka_message_producer(mocker):
    mock_producer = mocker.patch('kafka.KafkaProducer')
    mock_producer.return_value.send.return_value = None
    mock_producer.return_value.flush.return_value = None
    
    producer = KafkaMessageProducer()
    test_message = {"test": "message"}
    producer.send_message(test_message)
    
    mock_producer.return_value.send.assert_called_once_with('iot_data', test_message)
    mock_producer.return_value.flush.assert_called_once()