from soapi.nsr import Nsr
from soapi.nsd import Nsd
from soapi.identity import basic_token
from settings import OSM_ADMIN_CREDENTIALS, LOGGING
from actions.exceptions import *
import logging.config

logging.config.dictConfig(LOGGING)
logger = logging.getLogger("worker")


class Action:
    def __init__(self, nsd_name, ns_name, vim_account_name):
        """Constructor

        Args:
            nsd_name (str): The name of the NS descriptor
            ns_name (str): The name of the NS to be instantiated
            vim_account_name (str): The name of the VIM
        """
        self.nsd_name = nsd_name
        self.ns_name = ns_name
        self.vim_account_name = vim_account_name
        self.__token = basic_token(OSM_ADMIN_CREDENTIALS.get('username'), OSM_ADMIN_CREDENTIALS.get('username'))

    def execute(self):
        """Execute the instantiation of the NS"""
        nsd = Nsd(self.__token)
        nsd_descriptor = nsd.search(self.nsd_name)
        if not isinstance(nsd_descriptor, dict):
            raise NsDescriptorNotFound("Failed to find the NS descriptor: `{}` ".format(self.nsd_name))

        ns = Nsr(self.__token)
        ns_response = ns.instantiate(nsd_descriptor, self.ns_name, self.vim_account_name)
        if ns_response.status_code != 201:
            raise NsInstantiationNotCompleted(
                "Failed to instantiate the NS with name `{}` based on descriptor with name `{}` in "
                "VIM `{}`".format(self.ns_name, self.nsd_name, self.vim_account_name))
