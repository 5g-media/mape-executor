from settings import OSM_COMPONENTS, LOGGING
from httpclient.client import Client
import logging.config
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.config.dictConfig(LOGGING)
logger = logging.getLogger("osm")


class Vnfd(object):
    """VNF Descriptor Class.

    This class serves as a wrapper for the Virtual Network Function Descriptor (VNFD)
    part of the Northbound Interface (NBI) offered by OSM. The methods defined in this
    class help retrieve the VNFDs of OSM.

    Attributes:
        bearer_token (str): The OSM Authorization Token.

    Args:
        token (str): The OSM Authorization Token.
    """

    def __init__(self, token):
        """VNF Descriptor Class Constructor."""
        self.__client = Client(verify_ssl_cert=False)
        self.bearer_token = token

    def get_list(self):
        """Fetch a list of the VNF descriptors.

        Returns:
            object: A requests object that includes the list of VNFDs

        Examples:
            >>> from nbiapi.identity import bearer_token
            >>> from nbiapi.vnfd import Vnfd
            >>> from settings import OSM_ADMIN_CREDENTIALS
            >>> token = bearer_token(OSM_ADMIN_CREDENTIALS.get('username'), OSM_ADMIN_CREDENTIALS.get('password'))
            >>> vnfd = Vnfd(token)
            >>> response = vnfd.get_list()

        OSM Cli:
            $ osm vnfd-list
        """
        endpoint = '{}/osm/vnfpkgm/v1/vnf_packages'.format(OSM_COMPONENTS.get('NBI-API'))
        headers = {"Authorization": "Bearer {}".format(self.bearer_token), "Accept": "application/json"}
        response = self.__client.get(endpoint, headers)
        logger.debug("Request `GET {}` returns HTTP status `{}`, headers `{}` and body `{}`."
                     .format(response.url, response.status_code, response.headers, response.text))
        return response

    def get(self, vnfd_uuid=None):
        """Fetch details of a specific VNF descriptor.

        Args:
            vnfd_uuid (str): The UUID of the VNFD to fetch details for.

        Returns:
            object: A requests object.

        Examples:
            >>> from nbiapi.identity import bearer_token
            >>> from nbiapi.vnfd import Vnfd
            >>> from settings import OSM_ADMIN_CREDENTIALS
            >>> token = bearer_token(OSM_ADMIN_CREDENTIALS.get('username'), OSM_ADMIN_CREDENTIALS.get('password'))
            >>> vnfd = Vnfd(token)
            >>> response = vnfd.get(vnfd_uuid='f86e373e-850a-4df0-a354-aeba58684tdf6')

        OSM Cli:
            $ osm vnfd-show cirros_vnf
        """
        endpoint = '{}/osm/vnfpkgm/v1/vnf_packages/{}'.format(OSM_COMPONENTS.get('NBI-API'), vnfd_uuid)
        headers = {"Authorization": "Bearer {}".format(self.bearer_token), "Accept": "application/json"}
        response = self.__client.get(endpoint, headers)
        logger.debug("Request `GET {}` returns HTTP status `{}`, headers `{}` and body `{}`."
                     .format(response.url, response.status_code, response.headers, response.text))
        return response
