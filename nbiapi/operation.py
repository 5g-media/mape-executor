from httpclient.client import Client
import logging.config
import urllib3
from settings import OSM_COMPONENTS, LOGGING

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.config.dictConfig(LOGGING)
logger = logging.getLogger("osm")


class NsLcmOperation(object):
    """NsLcmOperation Class.

    Attributes:
        bearer_token (str): The OSM Authorization Token

    Args:
        token (str): The OSM Authorization Token
    """

    def __init__(self, token):
        """NS LCM Class Constructor."""
        self.__client = Client(verify_ssl_cert=False)
        self.bearer_token = token

    def get_list(self):
        """Fetch the list of operations

        Returns:
            object: A requests object

        Examples:
            >>> from nbiapi.identity import bearer_token
            >>> from nbiapi.operation import NsLcmOperation
            >>> from settings import OSM_ADMIN_CREDENTIALS
            >>> token = bearer_token(OSM_ADMIN_CREDENTIALS.get('username'), OSM_ADMIN_CREDENTIALS.get('username'))
            >>> ns_operation = NsLcmOperation(token)
            >>> request = ns_operation.get_list()
            >>> print(request.status_code)
            200

        """
        endpoint = '{}/osm/nslcm/v1/ns_lcm_op_occs'.format(OSM_COMPONENTS.get('NBI-API'))
        headers = {"Authorization": "Bearer {}".format(self.bearer_token), "Accept": "application/json",
                   "Content-Type": "application/json"}
        response = self.__client.list(endpoint, headers)
        logger.debug("Request `GET {}` returns HTTP status `{}`, headers `{}` and body `{}`."
                     .format(response.url, response.status_code, response.headers, response.text))
        return response

    def get(self, operation_uuid=None):
        """Fetch details of a specific operation

        Args:
            operation_uuid (str): The UUID of the performed operation

        Returns:
            object: A requests object

        Examples:
            >>> from nbiapi.identity import bearer_token
            >>> from nbiapi.operation import NsLcmOperation
            >>> from settings import OSM_ADMIN_CREDENTIALS
            >>> token = bearer_token(OSM_ADMIN_CREDENTIALS.get('username'), OSM_ADMIN_CREDENTIALS.get('username'))
            >>> ns_operation = NsLcmOperation(token)
            >>> request = ns_operation.get(operation_uuid='7a1bd53e-af29-40d6-bbde-ee8be69ddc3e')
            >>> print(request.status_code)
            200

        """
        endpoint = '{}/osm/nslcm/v1/ns_lcm_op_occs/{}'.format(OSM_COMPONENTS.get('NBI-API'), operation_uuid)
        headers = {"Authorization": "Bearer {}".format(self.bearer_token), "Accept": "application/json",
                   "Content-Type": "application/json"}
        response = self.__client.get(endpoint, headers)
        logger.debug("Request `GET {}` returns HTTP status `{}`, headers `{}` and body `{}`."
                     .format(response.url, response.status_code, response.headers, response.text))
        return response
