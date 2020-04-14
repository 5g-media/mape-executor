from settings import KAFKA_CONFIGURATION_TOPIC
from utils import init_producer


class Configuration:
    action_key = "vce"

    def __init__(self, mac):
        """ Configuration constructor

        Args:
            mac (str): The mac of the VDU
        """
        self.mac = mac
        self.action = {
            'id': self.mac
        }

    def set_bitrate(self, bitrate):
        """ Compose the configuration message to be sent on Kafka bus

        Args:
            bitrate (int): The profile to be applied in vCE

        Returns:
            bool: If the message published in kafka or not

        Examples:
            >>> from actions.vnf_configuration.vce import Configuration
            >>> vdu_uuid = "12:12:32:12:a1"
            >>> configuration = Configuration(vdu_uuid)
            >>> bitrate = 2213
            >>> configuration.set_bitrate(bitrate)

        """
        completed = True
        message = {
            "mac": self.mac,
            "action": {'bitrate': bitrate}
        }

        kafka_producer = init_producer()
        operation = kafka_producer.send(KAFKA_CONFIGURATION_TOPIC, value=message,
                                        key=self.action_key)
        try:
            operation.get(timeout=5)
        except Exception as ex:
            completed = False
        finally:
            kafka_producer.close()
            return completed
