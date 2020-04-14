from settings import OSM_COMPONENTS, LOGGING
from httpclient.client import Client
import logging.config
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.config.dictConfig(LOGGING)
logger = logging.getLogger("osm")


class Ns(object):
    """NS Class.

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
        """Fetch a list of all NS Instances

        Returns:
            object: A list of NSs as a requests object

        Examples:
            >>> from nbiapi.identity import bearer_token
            >>> from nbiapi.ns import Ns
            >>> from settings import OSM_ADMIN_CREDENTIALS
            >>> token = bearer_token(OSM_ADMIN_CREDENTIALS.get('username'), OSM_ADMIN_CREDENTIALS.get('username'))
            >>> ns = Ns(token)
            >>> response = ns.get_list()
            >>> print(response.json())

        OSM Cli:
            $ osm ns-list
        """
        endpoint = '{}/osm/nslcm/v1/ns_instances'.format(OSM_COMPONENTS.get('NBI-API'))
        headers = {"Authorization": "Bearer {}".format(self.bearer_token), "Accept": "application/json"}
        response = self.__client.get(endpoint, headers)
        logger.debug("Request `GET {}` returns HTTP status `{}`, headers `{}` and body `{}`."
                     .format(response.url, response.status_code, response.headers, response.text))
        return response

    def get(self, ns_uuid=None):
        """Fetch details of a specific NS Instance

        Args:
            ns_uuid (str): The UUID of the NS to fetch details for

        Returns:
            object: A requests object

        Examples:
            >>> from nbiapi.identity import bearer_token
            >>> from nbiapi.ns import Ns
            >>> from settings import OSM_ADMIN_CREDENTIALS
            >>> token = bearer_token(OSM_ADMIN_CREDENTIALS.get('username'), OSM_ADMIN_CREDENTIALS.get('username'))
            >>> ns = Ns(token)
            >>> response = ns.get(ns_uuid='07048175-660b-404f-bbc9-5be7581e74de')

        OSM Cli:
            $ osm ns-show 07048175-660b-404f-bbc9-5be7581e74de
        """
        endpoint = '{}/osm/nslcm/v1/ns_instances/{}'.format(OSM_COMPONENTS.get('NBI-API'), ns_uuid)
        headers = {"Authorization": "Bearer {}".format(self.bearer_token), "Accept": "application/json"}
        response = self.__client.get(endpoint, headers)
        logger.debug("Request `GET {}` returns HTTP status `{}`, headers `{}` and body `{}`."
                     .format(response.url, response.status_code, response.headers, response.text))
        return response

    def scale_vnf(self, ns_uuid, vnf_index, scaling_group_name, scale_out=True):
        """ Scale in or out in VNF level

        Args:
            ns_uuid (str): The NS uuid
            vnf_index (int): The VNF index to be scaled
            scaling_group_name (str): The name in the VNF scaling_group_descriptor
            scale_out (bool): Decide scale in or out action. By default, scale out is performed.

        Returns:
            object: A requests object

        Examples:
            >>> from nbiapi.identity import bearer_token
            >>> from nbiapi.ns import Ns
            >>> from settings import OSM_ADMIN_CREDENTIALS
            >>> token = bearer_token(OSM_ADMIN_CREDENTIALS.get('username'), OSM_ADMIN_CREDENTIALS.get('username'))
            >>> ns = Ns(token)
            >>> response = ns.scale_vnf(ns_uuid="199b1fcd-eb32-4c6f-b149-34410acc2a32", vnf_index=2, scaling_group_name="scale_by_one", scale_out=False)
            # >>> response = ns.scale_vnf(ns_uuid="199b1fcd-eb32-4c6f-b149-34410acc2a32", vnf_index=2, scaling_group_name="scale_by_one", scale_out=False)

        OSM Cli:
            $ osm vnf-scale <ns_uuid> <vnf_index> --scale-in # scale in
            Scaling group: <scaling_group_name>

            $ osm vnf-scale <ns_uuid> <vnf_index> --scale-out # scale out (default)
            Scaling group: <scaling_group_name>
        """
        endpoint = '{}/osm/nslcm/v1/ns_instances/{}/scale'.format(OSM_COMPONENTS.get('NBI-API'), ns_uuid)
        headers = {"Authorization": "Bearer {}".format(self.bearer_token), "Accept": "application/json"}

        # Set value based on scale action
        scale_action = "SCALE_IN"
        if scale_out:
            scale_action = "SCALE_OUT"

        payload = {
            "scaleVnfData": {
                "scaleVnfType": scale_action,
                "scaleByStepData": {
                    "member-vnf-index": str(vnf_index),
                    "scaling-group-descriptor": str(scaling_group_name)
                }
            },
            "scaleType": "SCALE_VNF"
        }
        response = self.__client.post(endpoint, headers, payload=json.dumps(payload))
        logger.debug("Request `POST {}` returns HTTP status `{}`, headers `{}` and body `{}`."
                     .format(response.url, response.status_code, response.headers, response.text))
        return response

    def terminate(self, ns_uuid=None):
        """Terminate a NS Instance.

        Args:
            ns_uuid (str): The UUID of the NS to terminate

        Returns:
            response (object): A requests object

        Examples:
            >>> from nbiapi.identity import bearer_token
            >>> from nbiapi.ns import Ns
            >>> from settings import OSM_ADMIN_CREDENTIALS
            >>> token = bearer_token(OSM_ADMIN_CREDENTIALS.get('username'), OSM_ADMIN_CREDENTIALS.get('username'))
            >>> ns = Ns(token)
            >>> response = ns.terminate(ns_uuid='07048175-660b-404f-bbc9-5be7581e74de')

        """
        endpoint = '{}/osm/nslcm/v1/ns_instances/{}/terminate'.format(OSM_COMPONENTS.get('NBI-API'), ns_uuid)
        headers = {"Authorization": "Bearer {}".format(self.bearer_token), "Accept": "application/json"}
        response = self.__client.post(endpoint, headers)
        logger.debug("Request `GET {}` returns HTTP status `{}`, headers `{}` and body `{}`."
                     .format(response.url, response.status_code, response.headers, response.text))
        return response
