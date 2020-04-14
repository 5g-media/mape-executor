"""
Copyright 2020 SingularLogic SA

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import time
import logging.config
import yaml
from utils import init_consumer, check_ping
from actions.vnf_configuration import vdns, vcache
from actions.utils import get_vcdn_net_interfaces
from actions.exceptions import VnfdUnexpectedStatusCode, VnfScaleNotCompleted, \
    vCacheConfigurationFailed, VdnsConfigurationFailed
from nbiapi.identity import bearer_token
from nbiapi.ns import Ns as NetworkService
from nbiapi.operation import NsLcmOperation
from influx.queries import get_last_operation, delete_operation_by_ns
from settings import OSM_ADMIN_CREDENTIALS, OSM_KAFKA_NS_TOPIC, LOGGING, OSM_KAFKA_SERVER, \
    vCDN_NSD_PREFIX

APP = "osm_kafka_subscriber"

logging.config.dictConfig(LOGGING)
logger = logging.getLogger('worker')


def main():
    """Main process"""
    kafka_consumer = init_consumer(kafka_server=OSM_KAFKA_SERVER, scope=APP)
    kafka_consumer.subscribe(pattern=OSM_KAFKA_NS_TOPIC)

    for msg in kafka_consumer:
        action = msg.key.decode('utf-8', 'ignore')
        # Process the message
        message = yaml.safe_load(msg.value.decode('utf-8', 'ignore'))

        logger.warning(message)

        if action == "scale":
            # Valid events are: SCALE_IN, SCALE_OUT
            pass

        elif action == "scaled":
            configure_vcdn_ns_after_scale_out(message)

        elif action == "instantiate":
            # future usage
            pass

        elif action == "instantiated":
            configure_vcdn_ns_after_instantiation(message)
            pass

        elif action == "terminate":
            configure_vcdn_ns_after_termination(message)

        elif action == "terminated":
            # future usage
            pass


def configure_vcdn_ns_after_scale_out(message):
    """ Configure the vCDN NS after scaling out operation in a regular edge vCache VNF

    Args:
        message (dict): The message of scaled event in ns topic
    """
    event_state = message.get('operationState', None)
    # Consider this action only if it is completed
    if event_state != "COMPLETED":
        return

    try:
        token = bearer_token(OSM_ADMIN_CREDENTIALS.get('username'),
                             OSM_ADMIN_CREDENTIALS.get('password'))
        # check nsd
        ns_uuid = message.get('nsr_id', None)
        nsd_ref_name = get_nsd_ref_name(token, ns_uuid)
        if not (nsd_ref_name and nsd_ref_name.startswith(vCDN_NSD_PREFIX)):
            return

        # Detect the event: SCALE_IN, SCALE_OUT or something else
        operation_uuid = message.get('nslcmop_id', None)
        event = get_scale_event(token, operation_uuid)
        # Configure the vCache & vDNS only if SCALE_OUT event
        if not event or event != "SCALE_OUT":
            return

        # Wait 10 seconds: ensure that the new vCache is up and running. Also, be sure
        # that the vnf record includes the IPv4 of the new vCache.
        time.sleep(10)

        # Discover the vcache_incremental_counter <N> & the net IFs for UC3
        net_interfaces, current_vdu_index = get_vcdn_net_interfaces(
            ns_uuid, search_for_mid_cache="vCache_mid_vdu", search_for_edge_cache="vCache_edge_vdu")
        edge_net_interfaces = net_interfaces.get('edge', {})
        mid_net_interfaces = net_interfaces.get('mid', {})
        vcache_incremental_counter = int(current_vdu_index) + 1
        # discover the CACHE_NET_IP for UC3
        mid_vcache_ip_cache_net = mid_net_interfaces.get('5GMEDIA-CACHE-NET', {}).get('ip-address',
                                                                                      None)
        # discover the MGMT_NET_IP for UC3
        edge_vcache_ip_mgmt_net = edge_net_interfaces.get('5GMEDIA_MGMT_NET', {}).get(
            'ip-address', None)
        # discover the CACHE_USER_IP for UC3
        edge_vcache_ip_user_net = edge_net_interfaces.get('5GMEDIA-USER-NET', {}).get('ip-address',
                                                                                      None)
        # Check edge vCache net availability using ping
        ping_edge_vcache_ip(edge_vcache_ip_mgmt_net)

        # Set day-1,2... vCache configuration - Try every 18 seconds - totally 3 minutes
        for i in range(1, 11):
            logger.debug("vCache configuration: Attempt #{}".format(i))
            if configure_edge_vcache(edge_vcache_ip_mgmt_net, mid_vcache_ip_cache_net,
                                     vcache_incremental_counter):
                break
            time.sleep(18)

        # Update the vDNS
        configure_vdns(edge_vcache_ip_user_net, vcache_incremental_counter)

    except (VnfdUnexpectedStatusCode, VnfScaleNotCompleted, vCacheConfigurationFailed,
            VdnsConfigurationFailed) as ex:
        logger.error(ex)
    except Exception as ex:
        logger.exception(ex)


def configure_vcdn_ns_after_instantiation(message):
    """ Configure the vCDN NS after its instantiation

    Args:
        message (dict): The message of instantiation event in ns topic
    """
    event_state = message.get('operationState', None)
    # Consider this action only if it is completed
    if event_state != "COMPLETED":
        return
    logger.info('A new vCDN service just instantiated. Status: {}'.format(event_state))

    try:
        token = bearer_token(OSM_ADMIN_CREDENTIALS.get('username'),
                             OSM_ADMIN_CREDENTIALS.get('password'))

        # check nsd
        ns_uuid = message.get('nsr_id', None)
        nsd_ref_name = get_nsd_ref_name(token, ns_uuid)
        if not (nsd_ref_name and nsd_ref_name.startswith(vCDN_NSD_PREFIX)):
            return

        logger.info('vCDN service uuid is {}'.format(ns_uuid))

        # Check if event is `instantiate`
        operation_uuid = message.get('nslcmop_id', None)
        event = get_event(token, operation_uuid)
        if not event or event != "instantiate":
            return

        # Wait 10 seconds: ensure that the new vCache is up and running. Also, be sure
        # that the vnf record includes the IPv4 of the new vCache.
        time.sleep(10)

        # Discover the vcache_incremental_counter <N> & the net IFs for UC3
        net_interfaces, current_vdu_index = get_vcdn_net_interfaces(
            ns_uuid, search_for_mid_cache="vCache_mid_vdu", search_for_edge_cache="vCache_edge_vdu")
        edge_net_interfaces = net_interfaces.get('edge', {})
        mid_net_interfaces = net_interfaces.get('mid', {})
        vcache_incremental_counter = int(current_vdu_index) + 1
        # discover the CACHE_NET_IP for UC3
        mid_vcache_ip_cache_net = mid_net_interfaces.get('5GMEDIA-CACHE-NET', {}).get('ip-address',
                                                                                      None)
        # discover the MGMT_NET_IP for UC3
        edge_vcache_ip_mgmt_net = edge_net_interfaces.get('5GMEDIA_MGMT_NET', {}).get(
            'ip-address', None)
        # discover the CACHE_USER_IP for UC3
        edge_vcache_ip_user_net = edge_net_interfaces.get('5GMEDIA-USER-NET', {}).get('ip-address',
                                                                                      None)
        # Check edge vCache net availability using ping
        ping_edge_vcache_ip(edge_vcache_ip_mgmt_net)

        # Set day-1,2... vCache configuration - Try every 18 seconds - totally 3 minutes
        for i in range(1, 10):
            logger.info("vCache VNF configuration: Attempt #{}".format(i))
            if configure_edge_vcache(edge_vcache_ip_mgmt_net, mid_vcache_ip_cache_net,
                                     vcache_incremental_counter):
                break
            time.sleep(10)

        # Update the vDNS
        configure_vdns(edge_vcache_ip_user_net, vcache_incremental_counter)

    except Exception as ex:
        logger.exception(ex)


def configure_vcdn_ns_after_termination(message):
    """ Configure the vCDN NS after its termination, especially the vDNS

    Args:
        message (dict): The message of termination event in ns topic
    """
    event_state = message.get('operationState', None)
    # Consider this action only if it is completed
    if event_state != "PROCESSING":
        return
    logger.info('A running vCDN service is terminating. Status: {}'.format(event_state))

    ns_uuid = message.get('nsInstanceId', None)
    logger.info('vCDN service uuid is {}'.format(ns_uuid))
    token = bearer_token(OSM_ADMIN_CREDENTIALS.get('username'),
                         OSM_ADMIN_CREDENTIALS.get('password'))
    # check nsd
    nsd_ref_name = get_nsd_ref_name(token, ns_uuid)
    if not (nsd_ref_name and nsd_ref_name.startswith(vCDN_NSD_PREFIX)):
        return

    try:
        # Check if event is `terminate`
        operation_uuid = message.get('id', None)
        logger.info("The operation uuid is {}".format(operation_uuid))
        event = get_event(token, operation_uuid)
        if not event or event != "terminate":
            return

        # update the vDNS properly
        clean_vdns_from_regular_vnfs(ns_uuid)

        # fetch the number of spawned faas vnfs from db and update the vDNS configuration properly
        last_operation = get_last_operation(ns_uuid)
        instances_number = last_operation.get('instance_number', 0)
        if instances_number > 0:
            # update the vDNS configuration by deleting the vDNS configuration
            # related to the faas edge vCaches
            clean_vdns_from_faas_vnfs(ns_uuid, instances_number)

    except Exception as ex:
        logger.exception(ex)


def get_nsd_ref_name(token, ns_uuid):
    """ Get the nsd reference name by ns identifier

    Args:
        token (str): the auth token in OSM
        ns_uuid (str): The identifier of the NS

    Returns:
        str: the nsd reference name
    """
    ns = NetworkService(token)
    request = ns.get(ns_uuid=ns_uuid)
    response = request.json()
    return response.get('nsd-name-ref', None)


def get_event(token, operation_uuid):
    """ Get the type of the event

    Args:
        token (str): the auth token in OSM
        operation_uuid (str): The identifier of the operation

    Returns:
        str: the instantiation event
    """
    ns_operation = NsLcmOperation(token)
    request = ns_operation.get(operation_uuid=operation_uuid)
    response = request.json()
    return response.get('operationParams', {}).get('lcmOperationType', None)


def get_scale_event(token, operation_uuid):
    """ Get the type of the scale event

    Args:
        token (str): the auth token in OSM
        operation_uuid (str): The identifier of the operation

    Returns:
        str: the scale event
    """
    ns_operation = NsLcmOperation(token)
    request = ns_operation.get(operation_uuid=operation_uuid)
    response = request.json()
    event = response.get('operationParams', {}).get('scaleVnfData', {}).get(
        'scaleVnfType', None)
    return event


def ping_edge_vcache_ip(edge_vcache_ip_mgmt_net):
    """ Check edge vCache net availability using ping

    Args:
        edge_vcache_ip_mgmt_net (str): The edge vCache IP in MGMT network
    """
    for attempt in range(1, 20):
        # Ping the new vCache
        vcache_ping_status = check_ping(edge_vcache_ip_mgmt_net)
        logger.info("Ping the vCache VNF IP in MGMT net: {} => {}".format(edge_vcache_ip_mgmt_net,
                                                                          vcache_ping_status))
        if vcache_ping_status:
            logger.info('Ping is available...')
            break
        # Try in 10 seconds
        time.sleep(10)


def configure_edge_vcache(edge_vcache_ip_mgmt_net, mid_vcache_ip_cache_net,
                          vcache_incremental_counter):
    """ Apply day 1, 2 vCache configuration

    Args:
        edge_vcache_ip_mgmt_net:
        mid_vcache_ip_cache_net:
        vcache_incremental_counter:

    Returns:
        bool: True for completion. Else, False.
    """
    completed = True
    try:
        vcache_conf = vcache.Configuration(edge_vcache_ip_mgmt_net, mid_vcache_ip_cache_net)
        vcache_conf.apply(vcache_incremental_counter)
        logger.info(
            "Edge vCache VNF with IP `{}` (MGMT network) has been configured wrt the mid vCache "
            "VNF with IP `{}` (CACHE network) and index `{}`."
            "".format(edge_vcache_ip_mgmt_net, mid_vcache_ip_cache_net, vcache_incremental_counter))
    except Exception as ex:
        logger.error(ex)
        completed = False
    finally:
        return completed


def configure_vdns(edge_vcache_ip_user_net, vcache_incremental_counter):
    """ Add entry in DNS for the new vCache

    Args:
        edge_vcache_ip_user_net (str): The edge vCache IP in USER network
        vcache_incremental_counter (int): The number of running edge vCaches
    """
    vdns_conf = vdns.Configuration()
    vdns_conf.add_vcache_entry(edge_vcache_ip_user_net, vcache_incremental_counter)
    logger.info("The vDNS VNF has been configured wrt the Edge vCache with IP `{}` in (USER "
                "network) and index {}.".format(edge_vcache_ip_user_net,
                                                vcache_incremental_counter))


def clean_vdns_from_regular_vnfs(ns_uuid):
    """  Update the vDNS configuration upon vCDN ns termination related to the regular vnfs

    Args:
        ns_uuid (str): The NS identifier

    Returns:
        None
    """
    instances_number = 0
    vdns_conf = vdns.Configuration()
    try:
        net_interfaces, current_vdu_index = get_vcdn_net_interfaces(
            ns_uuid, search_for_mid_cache="vCache_mid_vdu", search_for_edge_cache="vCache_edge_vdu")
        instances_number = int(current_vdu_index) + 1
    except Exception as ex:
        logger.exception("clean_vdns_from_regular_vnfs error: {}".format(ex))
    finally:
        for instance_number in range(1, int(instances_number) + 1):
            vdns_conf.delete_vcache_entry(instance_number)
            logger.info("Remove the regular Edge vCache VNF with N={} from vDNS VNF. Configuration "
                        "was sent to vDNS VNF".format(instance_number))


def clean_vdns_from_faas_vnfs(ns_uuid, instances_number):
    """ Update the vDNS configuration upon vCDN ns termination related to the faas vnfs

    Args:s
        ns_uuid (str): The NS identifier
        instances_number (int): The number of faas vnfs instances

    Returns:
        None
    """
    vdns_conf = vdns.Configuration()
    for instance_number in range(1, int(instances_number) + 1):
        try:
            # Delete the vDNS configuration related to the faas edge vCache
            vdns_conf.delete_faas_vcache_entry(instance_number)
            logger.info("Remove the FaaS Edge vCache VNF with N={} from vDNS VNF. Configuration "
                        "was sent to vDNS VNF".format(instance_number))
        except Exception as ex:
            logger.error(ex)

    try:
        # delete all records from the faas_operations measurement in db
        status = delete_operation_by_ns(ns_uuid)
        # logger.debug(
        #     'Delete the record from faas_operations measurement in influx related to the NS '
        #     '{}. Status: {}'.format(ns_uuid, status))
    except Exception as ex:
        logger.exception(ex)


if __name__ == '__main__':
    main()
