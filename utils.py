import os
import sys
import json
import uuid
from datetime import datetime, timedelta
from kafka import KafkaProducer, KafkaConsumer
from influxdb import InfluxDBClient
from settings import KAFKA_SERVER, KAFKA_CLIENT_ID, KAFKA_API_VERSION, KAFKA_GROUP_ID, \
    INFLUX_DATABASES


def init_consumer(kafka_server, scope):
    """ Init a Kafka consumer that consumes the optimization actions given scope (UC)

    See more: https://kafka-python.readthedocs.io/en/master/apidoc/KafkaConsumer.html

    Returns:
        Iterator:  A KafkaConsumer Iterator
    """
    consumer = KafkaConsumer(bootstrap_servers=kafka_server,
                             client_id=KAFKA_CLIENT_ID,
                             enable_auto_commit=True,
                             api_version=KAFKA_API_VERSION,
                             group_id=KAFKA_GROUP_ID[scope])
    return consumer


def init_producer():
    """ Init a Kafka Producer

    See more: https://kafka-python.readthedocs.io/en/master/apidoc/KafkaProducer.html

    Returns:
        Iterator: the Kafka producer
    """
    producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER,
                             api_version=KAFKA_API_VERSION,
                             value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                             key_serializer=lambda v: json.dumps(v).encode('utf-8'))
    return producer


def init_producer_without_value_serialiazer():
    """ Init a Kafka Producer

    See more: https://kafka-python.readthedocs.io/en/master/apidoc/KafkaProducer.html

    Returns:
        Iterator: the Kafka producer
    """
    producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER,
                             api_version=KAFKA_API_VERSION,
                             key_serializer=lambda v: json.dumps(v).encode('utf-8'))
    return producer


def get_host_type():
    """ Detect the type of the host machine

    Returns:
        str: The host type: win32, linux...
    """
    return sys.platform.lower()


def check_ping(ipv4):
    """ Ping a machine (VM) given its IPv4

    Args:
        ipv4 (str): The IPv4 of the machine that ping will be tested

    Returns:
        bool: the ping status. True if ipv4 is reachable. Otherwise, False.
    """
    host_type = get_host_type()
    ping_arg = 'n' if host_type == 'win32' else 'c'
    ping_status = not (os.system('ping -{} 1 {}'.format(ping_arg, ipv4)))
    return ping_status


def init_influx_client():
    """ Init an InfluxDB client

    Returns:
        obj: the client
    """
    influx_client = InfluxDBClient(host=INFLUX_DATABASES['default']['HOST'],
                                   port=INFLUX_DATABASES['default']['PORT'],
                                   username=INFLUX_DATABASES['default']['USERNAME'],
                                   password=INFLUX_DATABASES['default']['PASSWORD'],
                                   database=INFLUX_DATABASES['default']['NAME'], )
    return influx_client


def compose_optimization_event(kafka_message, event):
    """ Compose the optimization event

    Args:
        kafka_message (dict): The message from ns.instances.exec
        event (str): The optimization event

    Returns:
        list: one optimization event
    """

    vim = kafka_message.get('mano', {}).get('vim', {})
    network_service = kafka_message.get('mano', {}).get('ns', {})
    vnf = kafka_message.get('mano', {}).get('vnf', {})
    timestamp = get_utcnow_timestamp()

    description = "Not set"
    if event not in ["vnf_scale_out", "vnf_scale_in"]:
        value = kafka_message.get('execution', {}).get('value', "Not set")
        description = "{}".format(value)

    optimization_event = [
        {
            "measurement": "optimization_event",
            "time": timestamp,
            "tags": {
                "vim_type": vim['type'],
                "vim_name": vim.get('name'),
                "ns_uuid": network_service['id']
            },
            "fields": {
                "source_origin": vim.get('tag', ""),
                "ns_name": network_service.get('nsd_name', ""),
                "vnf_name": "{}.{}".format(vnf.get('vnfd_name', ""), vnf.get('index', "")),
                "metric": event,
                "value": description
            }
        }
    ]
    return optimization_event


def get_utcnow_timestamp():
    """ Get the current timestamp in UTC

    Returns:
        str: now in UTC
    """
    timestamp = datetime.utcnow()
    return timestamp.strftime('%Y-%m-%dT%H:%M:%S.%fZ')


def get_one_hour_ago():
    """ Get timestamp 1 hour ago in UTC

    Returns:
        str: now in UTC
    """
    timestamp = datetime.utcnow() - timedelta(minutes=59)
    return timestamp.strftime('%Y-%m-%dT%H:%M:%S.%fZ')


def generate_event_uuid():
    """ Generate the identifier of the event (FaaS)

    Returns:
        str: the event identifier
    """
    return str(uuid.uuid4()).replace('-', '')
