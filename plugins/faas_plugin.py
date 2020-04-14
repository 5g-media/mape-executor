from time import sleep
import logging.config
from actions.utils import get_faas_vcdn_net_interfaces
from actions import faas_action
from nbiapi.identity import bearer_token
from nbiapi.ns import Ns as NetworkService
from faasapi.ns_polling import NetworkServicePolling
from influx.queries import get_first_operation, get_last_operation, delete_operation, \
    store_operation
from utils import generate_event_uuid
from settings import OSM_ADMIN_CREDENTIALS, OSM_IP, OSM_FAAS_IP, OSM_FAAS_PORT, VDNS_IP, \
    VDNS_PORT, LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger("worker")


def execute_faas_vnf_scale_out(ns_name, ns_uuid, vnfd_uuid):
    """ Apply the FaaS VNF scale out (e.g. in vCDN NS)

    Args:
        ns_name (str): the NS name
        ns_uuid (str): The NS uuid
        vnfd_uuid (str): The VNFd uuid
    """
    if ns_name is None:
        ns_name = get_ns_name(ns_uuid)

    # Get the network interfaces' details and the existing FaaS edge vCache VNFs
    net_interfaces = get_faas_vcdn_net_interfaces(
        ns_uuid, search_for_mid_cache="vCache_mid_vdu", search_for_edge_cache="vCache_edge_vdu")
    mid_vcache_ip_cache_net = net_interfaces.get('mid', {}).get('5GMEDIA-CACHE-NET', {}).get(
        'ip-address', None)

    # Get the bootstrap details
    ns_poll = NetworkServicePolling(OSM_IP, OSM_FAAS_IP, OSM_FAAS_PORT, ns_name)
    # Polling attempts every 10 secs - do 20 attempts
    bootstrap_ingress_url = None
    for i in range(1, 20):
        bootstrap_ingress_url = ns_poll.get_bootstrap_ingress_url()
        if bootstrap_ingress_url is not None:
            break
        sleep(10)

    if bootstrap_ingress_url is None:
        logger.error('Fail to poll the bootstrap IngressUrl of the vCDN NS')
        return
    logger.info('The service-specific serverless orchestration host/port of the vCDN service {} '
                'was retrieved: {}.'.format(ns_uuid, bootstrap_ingress_url))

    # get the number of running FaaS edge vCache VFNss
    running_faas_edge_vcaches = 0
    target_vnfd = 'vcache_vnfd.2'
    vnfd_parts = target_vnfd.split('.')
    vnfd_name = vnfd_parts[0]
    vnfd_index = vnfd_parts[1]

    # Get the less recent event uuid related to a spawned vnf
    operation = get_last_operation(ns_uuid)
    instance_number = operation.get('instance_number', 0)
    vcache_incremental_counter = int(instance_number) + 1

    # generate a unique uuid for the spawn operation
    event_uuid = generate_event_uuid()

    # Apply the scale out through the FaaS VIM
    faas_vnf_scale = faas_action.Action(OSM_IP, ns_uuid, vnfd_uuid)
    faas_vnf_scale.set_bootstrap_ingress_url(bootstrap_ingress_url)
    status = faas_vnf_scale.spawn_edge_vcache_vnf(
        event_uuid, ns_name, mid_vcache_ip_cache_net, vcache_incremental_counter, VDNS_IP,
        VDNS_PORT, vnfd_name=vnfd_name, vnfd_index=vnfd_index)

    if int(status) == 200:
        store_operation('spawn_vcache', event_uuid, ns_name, ns_uuid, vcache_incremental_counter)


def execute_faas_vnf_scale_in(ns_name, ns_uuid, vnfd_uuid):
    """ Apply the FaaS VNF scale out (e.g. in vCDN NS)

    Args:
        ns_name (str): the NS name
        ns_uuid (str): The NS uuid
        vnfd_uuid (str): The VNFd uuid
    """
    if ns_name is None:
        ns_name = get_ns_name(ns_uuid)

    # Get the bootstrap details
    ns_poll = NetworkServicePolling(OSM_IP, OSM_FAAS_IP, OSM_FAAS_PORT, ns_name)
    # Polling attempts every 10 secs - do 20 attempts
    bootstrap_ingress_url = None
    for i in range(1, 20):
        bootstrap_ingress_url = ns_poll.get_bootstrap_ingress_url()
        if bootstrap_ingress_url is not None:
            break
        sleep(10)

    if bootstrap_ingress_url is None:
        logger.error('Fail to poll the bootstrap IngressUrl of the vCDN NS')
        return
    logger.info('The service-specific serverless orchestration host/port of the vCDN service {} '
                'was retrieved: {}.'.format(ns_uuid, bootstrap_ingress_url))

    # Get the less recent event uuid related to a spawned vnf
    operation = get_first_operation(ns_uuid)
    spawn_event_uuid = operation.get('event_uuid', None)
    instance_number = operation.get('instance_number', None)
    if spawn_event_uuid is None or instance_number is None:
        raise Exception('Failed to apply a FaaS scale in operation')

    # generate a unique uuid for the termination operation
    terminate_event_uuid = generate_event_uuid()

    # Apply the scale out through the FaaS VIM
    faas_vnf_scale = faas_action.Action(OSM_IP, ns_uuid, vnfd_uuid)
    faas_vnf_scale.set_bootstrap_ingress_url(bootstrap_ingress_url)
    status = faas_vnf_scale.terminate_edge_vcache(terminate_event_uuid, spawn_event_uuid, ns_name,
                                                  instance_number, VDNS_IP, VDNS_PORT)
    # Remove the record of the spawned vnf from the database
    if int(status) == 200:
        delete_operation(spawn_event_uuid)


def get_ns_name(ns_uuid):
    # Get the NS name based on the NS uuid
    token = bearer_token(OSM_ADMIN_CREDENTIALS.get('username'),
                         OSM_ADMIN_CREDENTIALS.get('password'))
    ns = NetworkService(token)
    response = ns.get(ns_uuid=ns_uuid)
    data = response.json()
    return data['name']
