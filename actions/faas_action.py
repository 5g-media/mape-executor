import logging.config
import requests
import json
from httpclient.client import Client
from settings import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger("worker")


class Action:
    class Operations:
        SPAWN_VCACHE = 'spawn_vcache'
        TERMINATE_VCACHE = 'terminate_vcache'
        SPAWN_TRANSCODER = 'spawn_transcoder'
        TERMINATE_TRANSCODER = 'terminate_transcoder'
        SPAWN_SPECTATOR = 'spawn_spectator'
        TERMINATE_SPECTATOR = 'terminate_spectator'

    class Vnfds:
        VTRANSCODER_GPU = '7a026afc-c3d6-4192-907d-fd70e361e8aa'  # transcoder_2_9_0_gpu_vnfd
        VTRANSCODER_CPU = '66e4db31-4d04-45c8-b3ed-48a2149163f8'  # transcoder_2_9_0_cpu_vnfd

    def __init__(self, osm_host, ns_uuid, vnfd_uuid):
        """Constructor

        Args:
            ns_uuid (str): The uuid of the ns record
            vnfd_uuid (str): The uuid of the VNFd record
        """
        self.__client = Client()
        self.osm_host = osm_host
        self.ns_uuid = ns_uuid
        self.vnfd_uuid = vnfd_uuid
        self.bootstrap_ingress_url = None

    def set_bootstrap_ingress_url(self, bootstrap_ingress_url):
        self.bootstrap_ingress_url = bootstrap_ingress_url

    def spawn_edge_vcache_vnf(self, event_uuid, ns_name, mid_cache_ip_mgmt_net,
                              vcache_incremental_counter, vdns_ip, vdns_port,
                              vnfd_name='vcache_vnfd', vnfd_index='2',
                              kafka_broker='192.168.111.17:9092'):
        """ Spawn a new Edge vCache using the FaaS

        Args:
            event_uuid (str): The event uuid
            ns_name (str): The NS name
            mid_cache_ip_mgmt_net (str): The Mid vCache IPv4 in MGMT Network
            vcache_incremental_counter (int): The number of the current FaaS Edge vCache
            vdns_ip (str): The vDNS host
            vdns_port (str): The vDNS port
            vnfd_name (str): The VNF descriptor name. Default is 'vcache_vnfd'.
            vnfd_index (str): The VNFd index. Default is '2'
            kafka_broker (str): Host and port of the Kafka broker. Default is '192.168.111.17:9092'

        Returns:
            int: the request status code

        Raises:
            requests.exceptions.HTTPError
        """
        endpoint = "{}/handlerequest".format(self.bootstrap_ingress_url)
        headers = {"Content-Type": "application/json"}
        payload = {
            "osm_ip": self.osm_host,
            "event_uuid": "{}".format(event_uuid),
            "osm_ns": ns_name,
            "operation": self.Operations.SPAWN_VCACHE,
            "vnfd_name": vnfd_name,
            "vnfd_index": vnfd_index,
            "origin_ip": mid_cache_ip_mgmt_net,
            "origin_port": "8080",
            "fqdn": "cdn-uhd.cache-faas-{}.5gmedia.lab".format(vcache_incremental_counter),
            "vdns_ip": vdns_ip,
            "vdns_port": vdns_port,
            "kafka_broker": kafka_broker
        }
        logger.info(
            '[Request-event-{}] Spawn/scale out the FaaS Edge vCache VNF {}. Send request to '
            'serverless orchestrator: {}'.format(event_uuid, vnfd_name, payload))
        request = requests.post(endpoint, json=payload)
        response_status = request.status_code
        logger.info('[Response-event-{}] Spawn/scale out the FaaS Edge vCache VNF {}. Response was '
                    'retrieved. HTTP status code is {}'.format(event_uuid, vnfd_name,
                                                               response_status))
        request.raise_for_status()
        return response_status

    def terminate_edge_vcache(self, terminate_event_uuid, spawn_event_uuid, ns_name,
                              vcache_incremental_counter, vdns_ip, vdns_port):
        """ Terminate a running FaaS vCache, result of scale out (spawn) event

        Args:
            terminate_event_uuid (str): The uuid of the termination event
            spawn_event_uuid (str): The uuid of the spawn event
            ns_name (str): The NS name
            vcache_incremental_counter (int): The number of the current FaaS Edge vCache
            vdns_ip (str): The vDNS host
            vdns_port (str): The vDNS port

        Returns:
            int: the request status code

        Raises:
            requests.exceptions.HTTPError
        """
        endpoint = "{}/handlerequest".format(self.bootstrap_ingress_url)
        headers = {"Content-Type": "application/json"}
        payload = {
            "osm_ip": self.osm_host,
            "event_uuid": "{}".format(terminate_event_uuid),
            "osm_ns": ns_name,
            "operation": self.Operations.TERMINATE_VCACHE,
            "fqdn": "cdn-uhd.cache-faas-{}.5gmedia.lab".format(vcache_incremental_counter),
            "vdns_ip": vdns_ip,
            "vdns_port": vdns_port,
            "uuid": "{}".format(spawn_event_uuid)
        }
        logger.info(
            '[Request-event-{}] Terminate the FaaS Edge vCache VNF spawned by event {}. Send '
            'request to serverless orchestrator: {}'.format(terminate_event_uuid,
                                                            spawn_event_uuid, payload))
        request = requests.post(endpoint, json=payload)
        response_status = request.status_code
        logger.info('[Response-event-{}] Terminate the FaaS Edge vCache VNF spawned by event {}. '
                    'Response was retrieved. HTTP status code is {}'.format(
            terminate_event_uuid, spawn_event_uuid, response_status))
        request.raise_for_status()
        return response_status

    def spawn_transcoder3d_vnf(self, event_uuid, ns_name, vnfd_index, player_id, produce_profile,
                               gpu=True, metrics_broker_ip='', metrics_broker_port=''):
        endpoint = '{}/handlerequest'.format(self.bootstrap_ingress_url)
        headers = {'Content-Type': 'application/json'}

        gpu_node = '1'
        vnfd_name = self.Vnfds.VTRANSCODER_GPU
        processor = 'GPU'
        if not gpu:
            vnfd_name = self.Vnfds.VTRANSCODER_CPU
            gpu_node = '0'
            processor = 'CPU'

        payload = {
            'osm_ip': self.osm_host,
            'event_uuid': event_uuid,
            'osm_ns': ns_name,
            'operation': self.Operations.SPAWN_TRANSCODER,
            'player_index': player_id,  # '1',
            'vnfd_name': vnfd_name,
            'vnfd_index': '{}'.format(vnfd_index),  # '2',
            'gpu_node': gpu_node,
            'produce_profile': '{}'.format(produce_profile),
            'metrics_broker_ip': metrics_broker_ip,
            'metrics_broker_port': metrics_broker_port
        }
        logger.info('[Request-event-{}] Spawn vTranscoder {} on {}. Payload: {}'.format(
            event_uuid, vnfd_name, processor, payload))
        request = requests.post(endpoint, json=payload)
        # request = self.__client.post(endpoint, headers=None, payload=json.dumps(payload))
        response_data = request.text
        response_status = request.status_code
        logger.info(
            '[Response-event-{}] Spawn vTranscoder {} on {}. HTTP status: {} - Data: {}'.format(
                event_uuid, vnfd_name, processor, response_status, response_data))
        request.raise_for_status()
        return response_status

    def terminate_transcoder3d_vnf(self, spawn_event_uuid, terminate_event_uuid, ns_name):
        endpoint = '{}/handlerequest'.format(self.bootstrap_ingress_url)
        headers = {'Content-Type': 'application/json'}
        payload = {
            'osm_ip': self.osm_host,
            'event_uuid': '{}'.format(terminate_event_uuid),
            'osm_ns': ns_name,
            'operation': self.Operations.TERMINATE_TRANSCODER,
            'uuid': '{}'.format(spawn_event_uuid)
        }

        logger.warning(
            '[Request-event-{}] Terminate vTranscoder spawned by event {}. Payload: {}'.format(
                terminate_event_uuid, spawn_event_uuid, payload))

        request = requests.post(endpoint, json=payload)
        # request = self.__client.post(endpoint, headers=None, payload=json.dumps(payload))
        response_status = request.status_code
        logger.warning(
            '[Response-event-{}] Terminate vTranscoder spawned by event {}. HTTP status: {} - Data: {}'.format(
                terminate_event_uuid, spawn_event_uuid, response_status, request.text))
        request.raise_for_status()
        return response_status
