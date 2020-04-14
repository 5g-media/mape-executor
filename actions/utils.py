from nbiapi.identity import bearer_token
from nbiapi.vnf import Vnf
from settings import OSM_ADMIN_CREDENTIALS


def get_vcdn_net_interfaces(ns_uuid, search_for_mid_cache="vCache-mid-vdu",
                            search_for_edge_cache="vCache-edge-vdu"):
    """ Get the network interfaces of scaled VNF as well as the current count-index

    Args:
        ns_uuid (str): The NS uuid, in which the scaled VNF belongs to
        search_for_mid_cache (str): Search for the Mid vCache by given explicit name
        search_for_edge_cache (str): Search for scaled Edge vCache by given explicit name

    Returns:
        tuple(dict, int): The details of the VNF interfaces including the VDU index in the VNF
        (
            {
              "edge": {
                "user": {
                  "mac-address": "fa:16:3e:0c:94:7f",
                  "ip-address": "192.168.252.12",
                  "name": "ens6",
                  "ns-vld-id": "user"
                },
                "cache": {
                  "mac-address": "fa:16:3e:4d:b9:64",
                  "ip-address": "192.168.253.9",
                  "name": "ens7",
                  "ns-vld-id": "cache"
                },
                "management": {
                  "mgmt-vnf": "true",
                  "mac-address": "fa:16:3e:99:33:43",
                  "ip-address": "192.168.111.29",
                  "name": "ens3",
                  "ns-vld-id": "management"
                }
              },
              "mid": {
                "management": {
                  "ip-address": "192.168.111.13",
                  "ns-vld-id": "management",
                  "name": "ens3",
                  "mac-address": "fa:16:3e:02:f5:1c",
                  "mgmt-vnf": true
                },
                "cache": {
                  "ip-address": "192.168.253.12",
                  "name": "ens6",
                  "ns-vld-id": "cache",
                  "mac-address": "fa:16:3e:60:5d:9d"
                },
                "origin": {
                  "ip-address": "192.168.254.5",
                  "name": "ens7",
                  "ns-vld-id": "origin",
                  "mac-address": "fa:16:3e:0d:64:97"
                }
              }
            },
            <int|1>
        )
    """
    vdus_list = []
    interfaces = {"mid": None, "edge": None}
    edges_interfaces_all = {}
    count_index = None

    # Fetch the VNFs by given NS instance
    token = bearer_token(OSM_ADMIN_CREDENTIALS.get('username'),
                         OSM_ADMIN_CREDENTIALS.get('password'))
    vnf = Vnf(token)
    response = vnf.get_list_by_ns(ns_uuid=ns_uuid)
    vnfs_list = response.json()

    # Keep the VDUs details
    for vnf_instance in vnfs_list:
        vdus_list += vnf_instance.get("vdur", [])

    # Discover the interfaces of the proper scaled Edge VNF and Mid vCache
    for vdu in vdus_list:
        # Get Mid vCache net details
        if vdu.get('vdu-id-ref', None) is not None and \
                vdu['vdu-id-ref'] == search_for_mid_cache and \
                vdu.get('count-index', None) == 0:
            interfaces['mid'] = format_vdu_interfaces(vdu.get('interfaces', []))

        # Get Edge vCache net details (the new one)

        if vdu.get('vdu-id-ref', None) is not None and \
                vdu['vdu-id-ref'] == search_for_edge_cache and \
                vdu.get('count-index', None) >= 0:
            edges_interfaces_all[str(vdu['count-index'])] = format_vdu_interfaces(
                vdu.get('interfaces', []))

    # Keep the VDU with the greatest count-index
    latest_vdu_index = max([int(k) for k in list(edges_interfaces_all.keys())])
    count_index = latest_vdu_index
    interfaces['edge'] = edges_interfaces_all[str(latest_vdu_index)]
    return interfaces, count_index


def get_faas_vcdn_net_interfaces(ns_uuid, search_for_mid_cache="vCache_mid_vdu",
                            search_for_edge_cache="vCache_edge_vdu"):
    """ Get the network interfaces of the VNF

    Args:
        ns_uuid (str): The NS uuid, in which the scaled VNF belongs to
        search_for_mid_cache (str): Search for the Mid vCache by given explicit name
        search_for_edge_cache (str): Search for scaled Edge vCache by given explicit name

    Returns:
        dict: The details of the VNF interfaces
        (
            {
              "edge": None,
              "mid": {
                "management": {
                  "ip-address": "192.168.111.13",
                  "ns-vld-id": "management",
                  "name": "ens3",
                  "mac-address": "fa:16:3e:02:f5:1c",
                  "mgmt-vnf": true
                },
                "cache": {
                  "ip-address": "192.168.253.12",
                  "name": "ens6",
                  "ns-vld-id": "cache",
                  "mac-address": "fa:16:3e:60:5d:9d"
                },
                "origin": {
                  "ip-address": "192.168.254.5",
                  "name": "ens7",
                  "ns-vld-id": "origin",
                  "mac-address": "fa:16:3e:0d:64:97"
                }
              }
            }
        )
    """
    vdus_list = []
    interfaces = {"mid": None, "edge": None}
    edges_interfaces_all = {}
    count_index = None

    # Fetch the VNFs by given NS instance
    token = bearer_token(OSM_ADMIN_CREDENTIALS.get('username'),
                         OSM_ADMIN_CREDENTIALS.get('password'))
    vnf = Vnf(token)
    response = vnf.get_list_by_ns(ns_uuid=ns_uuid)
    vnfs_list = response.json()

    # Keep the VDUs details
    for vnf_instance in vnfs_list:
        vdus_list += vnf_instance.get("vdur", [])

    # Discover the interfaces of the proper scaled Edge VNF and Mid vCache
    for vdu in vdus_list:
        # Get Mid vCache net details
        if vdu.get('vdu-id-ref', None) is not None and \
                vdu['vdu-id-ref'] == search_for_mid_cache and \
                vdu.get('count-index', None) == 0:
            interfaces['mid'] = format_vdu_interfaces(vdu.get('interfaces', []))

        # Get Edge vCache net details (the new one)
        if vdu.get('vdu-id-ref', None) is not None and \
                vdu['vdu-id-ref'] == search_for_edge_cache and \
                vdu.get('count-index', None) > 0:
            edges_interfaces_all[str(vdu['count-index'])] = format_vdu_interfaces(
                vdu.get('interfaces', []))

    return interfaces


def format_vdu_interfaces(interfaces_list):
    """ Convert the list of VDU interfaces in a dict using the name of the interfaces as keys

    Args:
        interfaces_list (list): The list of VDU net interfaces. Each item is a dict.

    Returns:
        dict: The interfaces as dict
        {
            "user": {
              "mac-address": "fa:16:3e:0c:94:7f",
              "ip-address": "192.168.252.12",
              "name": "ens6",
              "ns-vld-id": "user"
            },
            "cache": {
              "mac-address": "fa:16:3e:4d:b9:64",
              "ip-address": "192.168.253.9",
              "name": "ens7",
              "ns-vld-id": "cache"
            },
            "management": {
              "mgmt-vnf": "true",
              "mac-address": "fa:16:3e:99:33:43",
              "ip-address": "192.168.111.29",
              "name": "ens3",
              "ns-vld-id": "management"
            }
          }
    """
    interfaces = {}
    for interface in interfaces_list:
        net_type = interface.get('ns-vld-id', None)
        if net_type is None:
            continue
        interfaces[net_type] = interface
    return interfaces
