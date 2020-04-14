import logging.config
from utils import init_influx_client, get_utcnow_timestamp, get_one_hour_ago
from settings import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger("worker")


def store_operation(operation_type, event_uuid, ns_name, ns_uuid, instance_number):
    """ Store a faas operation like vcache spawn

    Args:
        operation_type (str): The type of the operation.
        event_uuid (str): the identifier of the event
        ns_name (str): the NS name
        ns_uuid (str): the NS identifier
        instance_number (int): The number of VNF instance

    Returns:
        None
    """
    influx_client = init_influx_client()
    timestamp = get_utcnow_timestamp()

    operation = [
        {
            "measurement": "faas_operations",
            "time": timestamp,
            "tags": {
                "operation_type": operation_type,
                "event_uuid": event_uuid,
                "ns_uuid": ns_uuid
            },
            "fields": {
                "ns_name": ns_name,
                "instance_number": int(instance_number)
            }
        }
    ]
    influx_client.write_points(operation)


def get_first_operation(ns_uuid):
    """ Fetch information for the less recent spawned event (the last hour)

    ns_uuid (str): The NS identifier

    Returns:
        dict: the event identifier and the FaaS VNF instance number
    """
    event_uuid, instance_number = None, None
    one_hour_ago = get_one_hour_ago()
    try:
        client = init_influx_client()
        query = "select * from faas_operations where time> '{}' and ns_uuid='{}' order by time asc limit 1".format(
            one_hour_ago, ns_uuid)
        response = client.query(query)
        series = response.raw['series']
        serie = series[0]
        values = serie['values']
        value = values[0]

        event_uuid = value[1]
        instance_number = value[2]
    except Exception as ex:
        logger.error(ex)
    finally:
        return {"event_uuid": event_uuid, "instance_number": instance_number}


def get_last_operation(ns_uuid):
    """ Fetch information for the most recent spawned event

    ns_uuid (str): The NS identifier

    Returns:
        dict: the event identifier and the FaaS VNF instance number
    """
    event_uuid, instance_number = None, 0
    try:
        client = init_influx_client()
        query = "select * from faas_operations where ns_uuid='{}' order by time desc limit 1".format(
            ns_uuid)
        response = client.query(query)
        series = response.raw['series']
        serie = series[0]
        values = serie['values']
        value = values[0]

        event_uuid = value[1]
        instance_number = value[2]
    except Exception as ex:
        logger.error(ex)
    finally:
        return {"event_uuid": event_uuid, "instance_number": instance_number}


def delete_operation(event_uuid):
    """ Drop a series from the faas_operations measurement by given the event uuid

    Args:
        event_uuid (str): The event uuid

    Returns:
        bool: True for success. Otherwise, False.
    """
    client = init_influx_client()
    query = "DROP SERIES FROM faas_operations WHERE event_uuid='{}'".format(event_uuid)
    response = client.query(query)
    return response.error is None


def delete_operation_by_ns(ns_uuid):
    """ Drop a series from the faas_operations measurement by given the NS uuid

    Args:
        ns_uuid (str): The NS uuid

    Returns:
        bool: True for success. Otherwise, False.
    """
    client = init_influx_client()
    query = "DROP SERIES FROM faas_operations WHERE ns_uuid='{}'".format(ns_uuid)
    response = client.query(query)
    return response.error is None
