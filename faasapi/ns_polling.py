import logging.config
from httpclient.client import Client
from settings import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger("worker")


class NetworkServicePolling:

    def __init__(self, osm_host, osm_faas_host, osm_faas_port, ns_name):
        """ Initialize the object

        Args:
            osm_host (str): The OSM host
            osm_faas_host (str): The FaaS VIM host (normally it is the same with OSM host)
            osm_faas_port (str): The FaaS VIM port
            ns_name (str): The NS name
        """
        self.__client = Client()
        self.osm_host = osm_host
        self.faas_polling_host = osm_faas_host
        self.faas_polling_ip = osm_faas_port
        self.bootstrap_ingress_url = None
        self.ns_name = ns_name

    def get_vnfs_info(self):
        """ Get information about the involved VNFs

        Returns:
            dict:

        Response Example:
        [
          {
            "vnf_name": "vcdn_bootstrap_vnfd.1",
            "status": "ACTIVE",
            "records": 0,
            "ip_address": "0.0.0.0"
          },
          {
            "vnf_name": "vcache_vnfd.2",
            "status": "ACTIVE",
            "records": 2,
            "ip_address": "0.0.0.0"
          },
          {
            "vnf_name": "vCache_mid_UC3_5GMEDIA.3",
            "status": "ACTIVE",
            "records": 0,
            "ip_address": "192.168.111.19"
          },
          {
            "vnf_name": "vCache_edge_UC3_5GMEDIA.4",
            "status": "ACTIVE",
            "records": 0,
            "ip_address": "192.168.111.27"
          }
        ]
        """
        vnfs_list = []
        endpoint = 'http://{}:{}/osm/{}'.format(self.faas_polling_host, self.faas_polling_ip,
                                                self.ns_name)
        request = self.__client.get(endpoint)
        response_status = request.status_code
        data = request.json()

        for vnf in data['vnfs']:
            vnf_name = vnf.get('vnf_name', None)
            ip_address = vnf.get('ip_address', None)
            status = vnf.get('status', None)
            vim_info = vnf.get('vim_info', {})
            records = 0
            if 'records' in vim_info.keys():
                records = len(vim_info['records'])
            vnf_entry = {'vnf_name': vnf_name, 'ip_address': ip_address, 'status': status,
                         'records': records}
            vnfs_list.append(vnf_entry)
        return vnfs_list

    def get_bootstrap_ingress_url(self):
        """ Get the Ingress Url of the bootstrap serverless VNF

        Returns:
            str: the Ingress Url of the bootstrap serverless VNF
        """
        bootstrap_ingress_url = None
        endpoint = 'http://{}:{}/osm/{}'.format(self.faas_polling_host, self.faas_polling_ip,
                                                self.ns_name)
        request = self.__client.get(endpoint)
        response_status = request.status_code
        data = request.json()

        if response_status != 200:
            return bootstrap_ingress_url

        for vnf in data['vnfs']:
            ingress_url = vnf.get('vim_info', {}).get('IngressUrl', None)
            if ingress_url is not None:
                bootstrap_ingress_url = ingress_url
                break
        return bootstrap_ingress_url

    def set_bootstrap_ingress_url(self, bootstrap_ingress_url):
        """
        Set the Ingress Url of the bootstrap serverless VNF
        """
        self.bootstrap_ingress_url = bootstrap_ingress_url
