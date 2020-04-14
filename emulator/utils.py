import json
from kafka import KafkaProducer, KafkaConsumer
from settings import KAFKA_SERVER, KAFKA_CLIENT_ID, KAFKA_API_VERSION


def init_producer():
    """ Launch a Kafka Producer

    Returns:
        Iterator: the Kafka producer
    """
    producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER,
                             api_version=KAFKA_API_VERSION,
                             value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                             key_serializer=lambda v: json.dumps(v).encode('utf-8'))
    return producer


def init_consumer(group_id):
    """ Launch a Kafka Consumer

    Returns:
        Iterator: the Kafka consumer
    """
    kconsumer = KafkaConsumer(bootstrap_servers=KAFKA_SERVER,
                             client_id=KAFKA_CLIENT_ID,
                             enable_auto_commit=True,
                             api_version=KAFKA_API_VERSION,
                             group_id=group_id)
    return kconsumer
