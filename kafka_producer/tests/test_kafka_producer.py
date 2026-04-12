def test_kafka_message_producer(mocker):
    # Patch where it is *used*, not where it is defined (PEP 8/mock best practice)
    mock_producer = mocker.patch("kafka_producer.KafkaProducer")
    mock_producer.return_value.send.return_value = None
    mock_producer.return_value.flush.return_value = None

    from kafka_producer import KafkaMessageProducer

    producer = KafkaMessageProducer()
    test_message = {"test": "message"}
    producer.send_message(test_message)

    # Default topic now matches the rest of the pipeline
    mock_producer.return_value.send.assert_called_once_with("iot-data", test_message)
    mock_producer.return_value.flush.assert_called_once()
