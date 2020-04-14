import json
import logging.config
from settings import LOGGING
from httpclient.client import Client as HttpClient
from actions.exceptions import vCacheConfigurationFailed

logging.config.dictConfig(LOGGING)
logger = logging.getLogger('worker')


class Configuration:
    def __init__(self, edge_vcache_ip_mgmt_network, mid_vcache_ip_cache_network):
        """Constructor

        Args:
            edge_vcache_ip_mgmt_network (str): The IP of the Edge vCache in the Management Network
            mid_vcache_ip_cache_network (str): The IP of the Mid vCache in the Cache Network
        """
        self.__client = HttpClient(verify_ssl_cert=False)
        self.ip_mgmt_network = edge_vcache_ip_mgmt_network
        self.ip_cache_network = mid_vcache_ip_cache_network
        self.port = "8888"

    def apply(self, vcache_incremental_counter):
        """ Apply the day 1/2 configuration after vCache instantiation

        Args:
            vcache_incremental_counter (int): incremental integer for each vCache edge
                added/scaled in the vCDN

        Returns:
            object: A requests object

        Raises:
            vCacheConfigurationFailed: The day 1, 2 configuration for vCache failed.

        Examples:
            >>> from actions.vnf_configuration import vcache
            >>> edge_vcache_ip_mgmt_network = "192.168.111.31"
            >>> mid_vcache_ip_cache_network = "192.168.253.12"
            >>> vcache_incremental_counter = 2
            >>> vcache_conf = vcache.Configuration(edge_vcache_ip_mgmt_network, mid_vcache_ip_cache_network)
            >>> request = vcache_conf.apply(vcache_incremental_counter)
            >>> request.status_code
            201
        """
        endpoint = 'http://{}:{}/vnfconfig/v1/cache_edge_origin_configuration'.format(
            self.ip_mgmt_network, self.port)
        headers = {"Accept": "application/json"}

        payload = {
            "vnfConfigurationData": {
                "vnfSpecificData": {
                    "ip_address": str(self.ip_cache_network),
                    "port": "8080",
                    "fqdn": "cdn-uhd.cache{}.5gmedia.lab".format(vcache_incremental_counter)
                }
            }
        }
        request = self.__client.patch(endpoint, headers, payload=json.dumps(payload))
        logger.debug(request.text)

        # The expected HTTP status code is 200. In any other case, raise an exception.
        if int(request.status_code) != 200:
            raise vCacheConfigurationFailed(
                "Failed to set the day 1, 2 configuration for vCache with N={}. The MGMT_NET was "
                "{} while the CACHE_NET was {}".format(self.ip_mgmt_network, self.ip_cache_network,
                                                       vcache_incremental_counter))

        return request
