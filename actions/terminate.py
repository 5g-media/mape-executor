from soapi.nsr import Nsr
from soapi.identity import basic_token
from settings import OSM_ADMIN_CREDENTIALS, LOGGING
from actions.exceptions import *
import logging.config

logging.config.dictConfig(LOGGING)
logger = logging.getLogger("worker")


class Action:
    def __init__(self, ns_uuid):
        """Constructor

        Args:
            ns_uuid (str): The id of the running NS
        """
        self.ns_uuid = ns_uuid
        self.__token = basic_token(OSM_ADMIN_CREDENTIALS.get('username'), OSM_ADMIN_CREDENTIALS.get('username'))

    def execute(self):
        """Execute the instantiation of the NS"""
        ns = Nsr(self.__token)
        ns_response = ns.terminate(self.ns_uuid)
        if ns_response.status_code != 201:
            raise NsTerminationNotCompleted("Failed to terminate the NS with name `{}`".format(self.ns_uuid))
