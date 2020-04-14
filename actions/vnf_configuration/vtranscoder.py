from settings import KAFKA_CONFIGURATION_TOPIC
from utils import init_producer


class Configuration:
    action_key = "faas"

    def __init__(self, ns_name, vnfd_name, vnf_index):
        """ Configuration constructor

        Args:
            ns_name (str): The name of the NS (not the uuid)
            vnfd_name (str): The name of the VNF descriptor
            vnf_index (int): The index of the VNF
        """
        self.ns_name = ns_name
        self.vnfd_name = vnfd_name
        self.vnf_index = vnf_index
        self.action = {
            'ns_name': self.ns_name,
            'vnf_name': self.vnfd_name,
            'vnf_index': '{}'.format(self.vnf_index)
        }

    def set_transcoder_profile(self, t_qualities):
        """ Compose the configuration message to be sent on Kafka bus

        The FaaS configuration service is used, as implemented from @IBM.

        Args:
            t_qualities (tuple): The qualities to be circulated in vTranscoder

        Returns:
            bool: If the message published in kafka or not

        Indicative message:
        {
          "ns_name": "ns_name|string",
          "vnf_name": "vnfd_name|name",
          "vnf_index": "integer",
          "action_params": {
            "produce_profiles": [
              0,
              2,
              4
            ]
          }
        }

        Examples:
            >>> from actions.vnf_configuration.vtranscoder import Configuration
            >>> ns_name = "ns_name_xxxx"
            >>> vnfd_name = "vnfd_name_xxx"
            >>> vnf_index = 1
            >>> configuration = Configuration(ns_name, vnfd_name, vnf_index)
            >>> profiles = (0,2,4)
            >>> configuration.set_transcoder_profile(profiles)
            True

        """
        completed = True
        qualities = list(t_qualities)

        # Append the profiles, proposed by the CNO
        if not isinstance(qualities, list):
            raise ValueError('Invalid input for vtranscoder qualities: {}'.format(qualities))
        if not len(qualities):
            raise ValueError('Empty list of vtranscoder qualities: {}'.format(qualities))

        action_parameters = {
            "produce_profiles": list(qualities)
        }
        self.action["action_params"] = action_parameters

        kafka_producer = init_producer()
        operation = kafka_producer.send(KAFKA_CONFIGURATION_TOPIC, value=self.action,
                                        key=self.action_key)
        try:
            operation.get(timeout=5)
        except Exception:
            completed = False
        finally:
            kafka_producer.close()
            return completed

    def apply_placement(self, processor="cpu"):
        """ Force vtranscoder placement: CPU vs GPU and vice versa.

        The FaaS configuration service is used, as implemented from @IBM.

        Args:
            processor (str): cpu or gpu

        Returns:
            bool: bool: If the message published in kafka or not

        Indicative sample:
        {
          "ns_name": "sky_balls",
          "vnf_name": "transcoder_2_8_4_vnfd",
          "vnf_index": "1",
          "invoker-selector": "cpu",
          "action-antiaffinity": "true",
          "action_params": {
            "gpu_node": "0"
          }
        }

        Examples:
            >>> from actions.vnf_configuration.vtranscoder import Configuration
            >>> ns_name = "ns_name_xxxx"
            >>> vnfd_name = "vnfd_name_xxx"
            >>> vnf_index = 1
            >>> configuration = Configuration(ns_name, vnfd_name, vnf_index)
            >>> configuration.apply_placement(processor="cpu")
            True

        """
        completed = True
        gpu_node = "0" if processor == "cpu" else "1"
        action_antiaffinity = "true"

        self.action["invoker-selector"] = processor
        self.action["action-antiaffinity"] = action_antiaffinity
        action_parameters = dict()
        action_parameters["gpu_node"] = gpu_node
        self.action["action_params"] = action_parameters

        kafka_producer = init_producer()
        operation = kafka_producer.send(KAFKA_CONFIGURATION_TOPIC, value=self.action,
                                        key=self.action_key)
        try:
            operation.get(timeout=5)
        except Exception:
            completed = False
        finally:
            kafka_producer.close()
            return completed

    def set_spectator_quality(self, cpu=True):
        """

        The configuration is consumed from the spectators through the kafka bus - not using
        the FaaS Conf service.

        Args:
            cpu:

        Returns:

        """
        completed = True
        processor = "cpu" if cpu else "gpu"

        configuration_message = {
            "annotations": [{
                "key": "placement",
                "value": {
                    "invoker-selector": {
                        "processor": processor
                    }
                },
                "action-antiaffinity": "true"
            }]
        }

        self.action["action_params"] = configuration_message

        kafka_producer = init_producer()
        operation = kafka_producer.send(KAFKA_CONFIGURATION_TOPIC, value=self.action,
                                        key=self.action_key)
        try:
            operation.get(timeout=5)
        except Exception:
            completed = False
        finally:
            kafka_producer.close()
            return completed
