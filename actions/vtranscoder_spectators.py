from settings import KAFKA_SPECTATOR_CONFIGURATION_TOPIC
from utils import init_producer


class Configuration:

    def __init__(self, qualities):
        """ Configuration constructor

        Args:
            qualities (dict): The spectators qualities to be applied. Sample:
                {
                  "clients": [
                    {
                      "client_id": "dfa65ec7d9a44a61b388cb65f8b29016",
                      "timestamp": 1558363628608378,
                      "use_these_qualities": [
                        {
                          "transcoder_id": "1",
                          "quality_id": 0,
                          "skip_frames": 1
                        },
                        {
                          "transcoder_id": "2",
                          "quality_id": 0,
                          "skip_frames": 1
                        }
                      ]
                    },
                    {
                      "client_id": 123456,
                      "timestamp": 1558363628608378,
                      "use_these_qualities": [
                        {
                          "transcoder_id": "1",
                          "quality_id": 0,
                          "skip_frames": 1
                        },
                        {
                          "transcoder_id": "2",
                          "quality_id": 0,
                          "skip_frames": 1
                        }
                      ]
                    }
                  ]
                }
        """
        self.qualities = qualities

    def set_spectators_profile(self):
        """ Compose the configuration message to be sent on Kafka bus

        Returns:
            bool: If the message published in kafka or not

        Examples:
            >>> from actions.vtranscoder_spectators import Configuration
            >>> qualities = {}
            >>> configuration = Configuration(qualities)
            >>> configuration.set_spectators_profile()

        """
        completed = True
        kafka_producer = init_producer()
        operation = kafka_producer.send(KAFKA_SPECTATOR_CONFIGURATION_TOPIC, value=self.qualities)
        try:
            operation.get(timeout=5)
        except Exception as e:
            completed = False
        finally:
            kafka_producer.close()
            return completed
