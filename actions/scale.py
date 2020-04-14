import logging.config
from nbiapi.ns import Ns
from nbiapi.vnfd import Vnfd
from nbiapi.vnf import Vnf
from nbiapi.operation import NsLcmOperation
from nbiapi.identity import bearer_token
from settings import OSM_ADMIN_CREDENTIALS, LOGGING
from actions.exceptions import ScalingGroupNotFound, VnfScaleNotCompleted, VnfdUnexpectedStatusCode

logging.config.dictConfig(LOGGING)
logger = logging.getLogger("worker")


class Action:
    def __init__(self, ns_uuid, vnfd_uuid):
        """Constructor

        Args:
            ns_uuid (str): The uuid of the ns record
            vnfd_uuid (str): The uuid of the VNFd record
        """
        self.ns_uuid = ns_uuid
        self.vnfd_uuid = vnfd_uuid
        self.__token = bearer_token(OSM_ADMIN_CREDENTIALS['username'],
                                    OSM_ADMIN_CREDENTIALS['password'])
        self.scaling_group_name = None
        self.get_scaling_group_if_any()

    def get_scaling_group_if_any(self):
        """ Get the scaling group by given VNF descriptor

        Returns:
            None

        Raises:
            VnfdUnexpectedStatusCode: The retrieval of the VNF descriptor was failed.
            ScalingGroupNotFound: Not found declared scaling group details in the VNF descriptor.
        """
        vnfd = Vnfd(self.__token)
        osm_request = vnfd.get(vnfd_uuid=self.vnfd_uuid)

        # Check the statue of the HTTP request
        if osm_request.status_code != 200:
            raise VnfdUnexpectedStatusCode(
                'The status code `{}` in the retrieval of VNFd details with UUID `{}` is '
                'not expected'.format(osm_request.status_code, self.vnfd_uuid))

        scaling_groups = []
        response = osm_request.json()
        scaling_group_descriptor = response.get('scaling-group-descriptor', [])

        for entry in scaling_group_descriptor:
            if 'name' in entry.keys():
                scaling_groups.append(entry.get('name'))

        if len(scaling_groups):
            # Todo: risky in case of multiple scaling group descriptors
            self.scaling_group_name = scaling_groups[0]
        else:
            raise ScalingGroupNotFound(
                'The scaling group of the VNFd `{}` has not been defined in the descriptor.'
                ''.format(self.vnfd_uuid))

    def allow_scale_action(self, scale_action="scale_out"):
        """ Allow or not the scale action.

        A scale-out action is allowed only if there is 1 edge vCache.
        A scale-in action is allowed only if there are 2 or more edge vCaches.

        Args:
            scale_action (str): the scale action

        Returns:
            bool: True to allow it. Otherwise, False.
        """
        vnf = Vnf(self.__token)
        response = vnf.get_list_by_ns(ns_uuid=self.ns_uuid)
        vnfs_list = response.json()

        current_edge_vdus = 1
        for vnf_instance in vnfs_list:
            if vnf_instance.get("member-vnf-index-ref", None) is not None and int(
                    vnf_instance["member-vnf-index-ref"]) == 2:
                current_edge_vdus = len(vnf_instance.get("vdur", []))

        if scale_action == "scale_out":
            return current_edge_vdus == 1
        elif scale_action == "scale_in":
            return current_edge_vdus > 1
        else:
            return False

    def detect_pending_scale_actions(self, scale_action="scale_out"):
        """ Detect if a scale in/out is pending

        Args:
            scale_action (str): the scale action

        Returns:
            bool: True if pending action is detected. Otherwise, False.
                If pending action is detected, the new action of same type must be skipped.

        """
        detected = False

        ns_operation = NsLcmOperation(self.__token)
        request = ns_operation.get_list()
        operations_list = request.json()

        for operation in operations_list:
            if operation['nsInstanceId'] != self.ns_uuid:
                continue
            if operation['lcmOperationType'] != "scale":
                continue
            if operation['operationState'] == "PROCESSING":
                action = operation.get('operationParams', {}).get('scaleVnfData', {}).get(
                    'scaleVnfType', None)
                if action is None:
                    continue

                action = action.lower()
                if action == scale_action:
                    detected = True
                    break

        return detected

    def apply(self, vnf_index, scale_action="scale_out"):
        """ Apply the scaling in or out

        Args:
            vnf_index (int): The VNF index
            scale_action (str): Scale in or out

        Returns:
            None

        Raises:
            VnfScaleNotCompleted: The scale action in VNF-level was failed.

        Examples:
            >>> from actions import scale as vnf_scale_action
            >>> ns_uuid = "xxxx"
            >>> vnfd_uuid = "yyyy"
            >>> vnf_index = 2
            >>> vnf_scale = vnf_scale_action.Action(ns_uuid, vnfd_uuid)
            >>> vnf_scale.apply(vnf_index, scale_action="scale_out")
        """
        scale_out = True if scale_action == "scale_out" else False

        if not self.allow_scale_action(scale_action=scale_action):
            raise VnfScaleNotCompleted(
                'The scaling action of the VNF with index `{}` (part of NS with uuid `{}`) is '
                'not allowed due to the number of edge vCaches.'.format(vnf_index,
                                                                        self.ns_uuid))

        if self.detect_pending_scale_actions(scale_action=scale_action):
            raise VnfScaleNotCompleted(
                'The scaling action of the VNF with index `{}` (part of NS with uuid `{}`) is '
                'not allowed since a pending `{}` was detected.'.format(vnf_index, self.ns_uuid,
                                                                        scale_action))

        network_service = Ns(self.__token)
        scale_request = network_service.scale_vnf(ns_uuid=self.ns_uuid, vnf_index=vnf_index,
                                                  scaling_group_name=self.scaling_group_name,
                                                  scale_out=scale_out)

        if int(scale_request.status_code) != 201:
            raise VnfScaleNotCompleted(
                'The status code `{}` in the scaling action of the VNF with index `{}` (part '
                'of NS with uuid `{}`) is not expected. '.format(scale_request.status_code,
                                                                 vnf_index, self.ns_uuid))
