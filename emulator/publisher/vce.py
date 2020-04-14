import json
from kafka.errors import KafkaError
from emulator.utils import init_producer
from settings import KAFKA_CONFIGURATION_TOPIC

"""
Indicative examples of day-1 configuration message in UC2/vCompressionEngine
"""

KEY = "vce"
VDU_UUID = "312312312123"
optimization_actions = [
    {
        "ip": "192.168.1.1",
        "vdu_uuid": VDU_UUID,
        "action": {
            "bitrate": "39"
        }
    },
    {
        "ip": "192.168.1.1",
        "vdu_uuid": VDU_UUID,
        "action": {
            "bitrate": "22.1"
        }
    },
    {
        "ip": "192.168.1.1",
        "vdu_uuid": VDU_UUID,
        "action": {
            "bitrate": "19.8"
        }
    }
]


def main():
    """Main process"""
    kafka_producer = init_producer()
    for action in optimization_actions:
        print(action)
        t = kafka_producer.send(KAFKA_CONFIGURATION_TOPIC, value=action, key=KEY)
        try:
            t.get(timeout=5)
        except KafkaError as e:
            pass
    kafka_producer.close()


if __name__ == '__main__':
    main()
