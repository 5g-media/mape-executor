"""
Copyright 2020 SingularLogic SA

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import json
import logging.config
from utils import init_consumer, init_influx_client, compose_optimization_event
from actions import scale as vnf_scale_action, vtranscoder_spectators
from actions.vnf_configuration import vdns, vce, vtranscoder
from actions.exceptions import VnfdUnexpectedStatusCode, ScalingGroupNotFound, \
    vCacheConfigurationFailed, VdnsConfigurationFailed, TranscoderProfileUpdateFailed, \
    TranscoderPlacementFailed, CompressionEngineConfigurationFailed, VnfScaleNotCompleted, \
    TranscoderSpectatorsQualityConfigurationFailed, InvalidTranscoderSpectatorsQualities
from plugins import faas_plugin
from actions.utils import get_vcdn_net_interfaces
from settings import KAFKA_EXECUTION_TOPIC, LOGGING, KAFKA_SERVER

APP = "worker"

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(APP)


def main():
    """Main process"""
    kafka_consumer = init_consumer(kafka_server=KAFKA_SERVER, scope=APP)
    kafka_consumer.subscribe(pattern=KAFKA_EXECUTION_TOPIC)

    for msg in kafka_consumer:
        try:
            # Process the message
            message = json.loads(msg.value.decode('utf-8', 'ignore'))
            # Get the action to be applied
            action = message.get('execution', {}).get('planning', None)
            if action is None:
                continue

            action_to_be_applied = message.get('analysis', {}).get('action', False)
            if not action_to_be_applied:
                continue

            influx_client = init_influx_client()

            if action == "vnf_scale_out":
                try:
                    ns_uuid = message.get('mano', {}).get('ns', {}).get('id', None)
                    vnfd_uuid = message.get('mano', {}).get('vnf', {}).get('vnfd_id', None)
                    vnf_index = message.get('mano', {}).get('vnf', {}).get('index', None)

                    # Execute the scaling out - Launch new VDU
                    vnf_scale = vnf_scale_action.Action(ns_uuid, vnfd_uuid)
                    vnf_scale.apply(vnf_index, scale_action="scale_out")

                    # Two steps must be performed when the new VM will be spawn and the edge
                    # vCache will be operational:
                    # (1) the mid vCache configuration, and
                    # (2) the vDNS configuration
                    # Both of them will be performed through the `osm_subscriber` after a
                    # relevant event in the intra-OSM kafka bus `ns` topic.

                    # Store the optimization events
                    # influx_client = init_influx_client()
                    optimization_event = compose_optimization_event(message, action)
                    influx_client.write_points(optimization_event)

                except (VnfdUnexpectedStatusCode, ScalingGroupNotFound, VnfScaleNotCompleted,
                        vCacheConfigurationFailed,
                        VdnsConfigurationFailed) as ex:
                    logger.error(ex)
                except Exception as ex:
                    logger.exception(ex)

            elif action == "vnf_scale_in":
                try:
                    ns_uuid = message.get('mano', {}).get('ns', {}).get('id', None)
                    vnfd_uuid = message.get('mano', {}).get('vnf', {}).get('vnfd_id', None)
                    vnf_index = message.get('mano', {}).get('vnf', {}).get('index', None)

                    # Discover the vcache_incremental_counter <N> & the CACHE_USER_IP for UC3
                    net_interfaces, current_vdu_index = get_vcdn_net_interfaces(ns_uuid)
                    edge_vcache_ip_user_net = net_interfaces.get('user', {}).get('ip-address', None)
                    vcache_incremental_counter = int(current_vdu_index) + 1

                    # Execute the scaling in - Remove VDU
                    vnf_scale = vnf_scale_action.Action(ns_uuid, vnfd_uuid)
                    vnf_scale.apply(vnf_index, scale_action="scale_in")
                    # Remove existing entry in DNS for the new vCache
                    vdns_conf = vdns.Configuration(edge_vcache_ip_user_net)
                    vdns_conf.delete_vcache_entry(vcache_incremental_counter)

                    # Store the optimization events
                    # influx_client = init_influx_client()
                    optimization_event = compose_optimization_event(message, action)
                    influx_client.write_points(optimization_event)

                except (VnfdUnexpectedStatusCode, ScalingGroupNotFound, VnfScaleNotCompleted,
                        VdnsConfigurationFailed) as ex:
                    logger.error(ex)
                except Exception as ex:
                    logger.exception(ex)

            elif action == "faas_vnf_scale_out":
                try:
                    ns_name = message.get('mano', {}).get('ns', {}).get('name', None)
                    ns_uuid = message.get('mano', {}).get('ns', {}).get('id', None)
                    vnfd_uuid = message.get('mano', {}).get('vnf', {}).get('vnfd_id', None)

                    logger.info('Scale out action was sent by the SS-CNO for the vCDN service {} '
                                'and uuid {}'.format(ns_name, ns_uuid))

                    # Apply faas scale out action
                    faas_plugin.execute_faas_vnf_scale_out(ns_name, ns_uuid, vnfd_uuid)
                    # Store the optimization events
                    optimization_event = compose_optimization_event(message, action)
                    influx_client.write_points(optimization_event)
                    logger.info('Event was stored in the database')
                except Exception as ex:
                    logger.exception(ex)

            elif action == "faas_vnf_scale_in":
                # future usage: use terminate operation
                try:
                    ns_name = message.get('mano', {}).get('ns', {}).get('name', None)
                    ns_uuid = message.get('mano', {}).get('ns', {}).get('id', None)
                    vnfd_uuid = message.get('mano', {}).get('vnf', {}).get('vnfd_id', None)

                    logger.info('Scale in action was sent by the SS-CNO for the vCDN service {} '
                                'and uuid {}'.format(ns_name, ns_uuid))

                    # Apply faas scale in action
                    faas_plugin.execute_faas_vnf_scale_in(ns_name, ns_uuid, vnfd_uuid)
                    # Store the optimization events
                    optimization_event = compose_optimization_event(message, action)
                    influx_client.write_points(optimization_event)
                    logger.info('Event was stored in the database')
                except Exception as ex:
                    logger.exception(ex)

            elif action == "set_vce_bitrate":
                try:
                    # Pick the profile or bitrate value
                    bitrate = message.get('execution', {}).get('value', None)
                    # fixme: when vCE is deployed through OSM
                    vdu_uuid = message.get('execution', {}).get('mac', None)

                    if int(bitrate) < 0:
                        logger.warning(
                            "The suggested vCE bitrate is negative (actual value: {})".format(
                                bitrate))
                        continue

                    # Apply the new vCE profile
                    configuration = vce.Configuration(vdu_uuid)
                    completed = configuration.set_bitrate(bitrate)
                    if not completed:
                        raise CompressionEngineConfigurationFailed('Failed to set the vCE profile')

                    # Store the optimization events
                    # optimization_event = compose_optimization_event(message, action)
                    # influx_client.write_points(optimization_event)

                except CompressionEngineConfigurationFailed as ex:
                    logger.error(ex)
                except Exception as ex:
                    logger.exception(ex)

            elif action == "set_vtranscoder_profile":
                try:
                    # Pick the profiles
                    qualities = message.get('execution', {}).get('value', [])
                    ns_name = message.get('mano', {}).get('ns', {}).get('name', None)
                    vnfd_name = message.get('mano', {}).get('vnf', {}).get('vnfd_name', None)
                    vnf_index = message.get('mano', {}).get('vnf', {}).get('index', None)

                    # Apply the new vTranscoder profile
                    configuration = vtranscoder.Configuration(ns_name, vnfd_name, vnf_index)
                    completed = configuration.set_transcoder_profile(tuple(qualities))
                    logger.debug(
                        "Action {} with status {}. Configuration: {}".format(action, completed,
                                                                             qualities))
                    if not completed:
                        raise TranscoderProfileUpdateFailed(
                            'Failed to set the vTranscoder qualities {}'.format(qualities))

                    # Store the optimization events
                    # influx_client = init_influx_client()
                    optimization_event = compose_optimization_event(message, action)
                    influx_client.write_points(optimization_event)

                except TranscoderProfileUpdateFailed as ex:
                    logger.error(ex)
                except Exception as ex:
                    logger.exception(ex)

            elif action == "set_vtranscoder_processing_unit":
                try:
                    # Pick the processor: "cpu|gpu"
                    processor = message.get('execution', {}).get('value', "cpu")
                    ns_name = message.get('mano', {}).get('ns', {}).get('name', None)
                    vnfd_name = message.get('mano', {}).get('vnf', {}).get('vnfd_name', None)
                    vnf_index = message.get('mano', {}).get('vnf', {}).get('index', None)

                    # Transcoder placement (CPU or GPU)
                    configuration = vtranscoder.Configuration(ns_name, vnfd_name, vnf_index)
                    completed = configuration.apply_placement(processor=processor)
                    logger.debug(
                        "Action {} with status {}. Configuration: {}".format(action, completed,
                                                                             processor))
                    if not completed:
                        raise TranscoderPlacementFailed(
                            "Failed apply the vTranscoder placement in {} processor".format(
                                processor))

                    # Store the optimization events
                    # influx_client = init_influx_client()
                    optimization_event = compose_optimization_event(message, action)
                    influx_client.write_points(optimization_event)

                except TranscoderPlacementFailed as ex:
                    logger.error(ex)
                except Exception as ex:
                    logger.exception(ex)

            elif action == "set_vtranscoder_client_profile":
                try:
                    # Fetch the spectators profile
                    spectators_qualities = message.get('execution', {}).get('value', {})
                    if not len(spectators_qualities.keys()) or \
                            spectators_qualities.get('clients', None) is None or \
                            not len(spectators_qualities['clients']):
                        raise InvalidTranscoderSpectatorsQualities(
                            'Invalid input for the spectators qualities in vTranscoder{}'.format(
                                spectators_qualities))
                    configuration = vtranscoder_spectators.Configuration(spectators_qualities)
                    completed = configuration.set_spectators_profile()
                    logger.debug(
                        "Action {} with status {}. Configuration: {}".format(action, completed,
                                                                             spectators_qualities))
                    if not completed:
                        raise TranscoderSpectatorsQualityConfigurationFailed(
                            'Failed to set the spectators qualities in vTranscoder{}'.format(
                                spectators_qualities))
                except TranscoderSpectatorsQualityConfigurationFailed as ex:
                    logger.error(ex)
                except InvalidTranscoderSpectatorsQualities as ex:
                    logger.error(ex)
                except Exception as ex:
                    logger.exception(ex)

            elif action == "ns_scale":
                # TODO: future usage
                pass

            elif action == "ns_instantiate":
                # TODO: future usage
                pass

            elif action == "ns_terminate":
                # TODO: future usage
                pass

            # raise Exception('Action {} is not supported'.format(action))

        except json.decoder.JSONDecodeError as ex:
            logger.warning("JSONDecodeError: {}".format(ex))
        except Exception as ex:
            logger.exception(ex)


if __name__ == '__main__':
    main()
