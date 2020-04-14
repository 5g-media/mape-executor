import json
import logging.config
from settings import LOGGING, VDNS_IP
from httpclient.client import Client as HttpClient
from actions.exceptions import VdnsConfigurationFailed

logging.config.dictConfig(LOGGING)
logger = logging.getLogger("worker")


class Configuration:
    def __init__(self):
        """
        Constructor
        """
        self.__client = HttpClient(verify_ssl_cert=False)
        self.vdns_ip = VDNS_IP
        self.vdns_port = "9999"
        self.headers = {"X-Api-Key": "secret", "Content-Type": "application/json"}

    def add_vcache_entry(self, edge_vcache_ip_user_network, vcache_incremental_counter):
        """ Add an entry for the new vCache after its instantiation

        Args:
            edge_vcache_ip_user_network (str): the IPv4 of edge vCache in User network
            vcache_incremental_counter (int): incremental integer for each vCache edge
                added/scaled in the vCDN

        Returns:
            object: A requests object

        Raises:
            VdnsConfigurationFailed: The The vDNS configuration after the instantiation of a
                new vCache failed.

        Examples:
            >>> from actions.vnf_configuration import vdns
            >>> vcache_ip_user_network ="192.168.252.3"
            >>> vcache_incremental_counter = 2
            >>> vdns_conf = vdns.Configuration()
            >>> vdns_conf.add_vcache_entry(vcache_ip_user_network, vcache_incremental_counter)
        """
        endpoint = 'http://{}:{}/dns'.format(self.vdns_ip, self.vdns_port)

        payload = {
            "hostname": "cdn-uhd.cache{}.5gmedia.lab".format(vcache_incremental_counter),
            "ip": "{}".format(edge_vcache_ip_user_network)
        }
        request = self.__client.post(endpoint, headers=self.headers, payload=json.dumps(payload))
        logger.debug("Request `POST {}` returns HTTP status `{}`, headers `{}` and body `{}`."
                     .format(request.url, request.status_code, request.headers, request.text))

        if request.status_code != 200:
            raise VdnsConfigurationFailed(
                "The vDNS configuration after the instantiation of the vCache with index={} "
                " failed".format(vcache_incremental_counter))
        return request

    def delete_vcache_entry(self, vcache_incremental_counter):
        """ Remove the existing entry of vCache after its deletion

        Args:
            vcache_incremental_counter (int): incremental integer for each vCache edge
                added/scaled in the vCDN

        Returns:
            object: A requests object

        Raises:
            VdnsConfigurationFailed: The The vDNS configuration after the deletion of an
                existing vCache failed.

        Examples:
            >>> from actions.vnf_configuration import vdns
            >>> vcache_ip_user_network ="192.168.252.12"
            >>> vcache_incremental_counter = 2
            >>> vdns_conf = vdns.Configuration(vcache_ip_user_network)
            >>> req = vdns_conf.delete_vcache_entry(vcache_incremental_counter)
            >>> req.status_code
            200
        """
        endpoint = 'http://{}:{}/dns'.format(self.vdns_ip, self.vdns_port)

        payload = {"hostname": "cdn-uhd.cache{}.5gmedia.lab".format(vcache_incremental_counter)}
        request = self.__client.delete(endpoint, headers=self.headers, payload=json.dumps(payload))
        logger.info("Request `DELETE {}` returns HTTP status `{}`, headers `{}` and body `{}`."
                    .format(request.url, request.status_code, request.headers, request.text))
        if request.status_code != 200:
            raise VdnsConfigurationFailed(
                "The vDNS configuration after the deletion of the vCache with index={} "
                "failed".format(vcache_incremental_counter))
        return request

    def delete_faas_vcache_entry(self, vcache_incremental_counter):
        """ Remove the existing entry of vCache after its deletion

        Args:
            vcache_incremental_counter (int): incremental integer for each vCache edge
                added/scaled in the vCDN

        Returns:
            object: A requests object

        Raises:
            VdnsConfigurationFailed: The The vDNS configuration after the deletion of an
                existing faas vCache failed.

        Examples:
            >>> from actions.vnf_configuration import vdns
            >>> vcache_ip_user_network ="192.168.252.12"
            >>> vcache_incremental_counter = 2
            >>> vdns_conf = vdns.Configuration(vcache_ip_user_network)
            >>> req = vdns_conf.delete_faas_vcache_entry(vcache_incremental_counter)
            >>> req.status_code
            200
        """
        endpoint = 'http://{}:{}/dns'.format(self.vdns_ip, self.vdns_port)
        payload = {
            "hostname": "cdn-uhd.cache-faas-{}.5gmedia.lab".format(vcache_incremental_counter)}
        request = self.__client.delete(endpoint, headers=self.headers, payload=json.dumps(payload))

        if request.status_code != 200:
            raise VdnsConfigurationFailed(
                "The vDNS configuration after the deletion of the vCache with index={} "
                "failed".format(vcache_incremental_counter))
        return request
