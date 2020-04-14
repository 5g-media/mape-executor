import json
from kafka.errors import KafkaError
from emulator.utils import init_producer
from settings import KAFKA_CONFIGURATION_TOPIC

'''
An example that sends two day1 configuration messages.

Note: It is assumed that a network service named: 'sky_balls' already instantiated with
      two FaaS vnfd-id of faas_vtranscoder_2_7_2_edge1_vnfd at index '1' and '2'.
'''

day_1_payload = [
    {
        "ns_name": "sky_balls",
        "vnf_name": "faas_vtranscoder_2_7_2_edge1_vnfd",
        "vnf_index": "1",
        "action_params": {
            "produce_profiles": [1, 2, 3]
        }
    },
    {
        "ns_name": "sky_balls",
        "vnf_name": "faas_vtranscoder_2_7_2_edge1_vnfd",
        "vnf_index": "2",
        "action_params": {
            "produce_profiles": [1, 4]
        }
    }
]

'''
An example that sends two day1 replacement messages to CPU node instantiating one with
an overridden parameter value and second with no parameter leading to preserving with
the ones set previously.

Note: It is assumed that a network service named: 'sky_balls' already instantiated with
      two FaaS vnfd-id of faas_vtranscoder_2_7_2_edge1_vnfd at index '1' and '2'.
'''

day_1_nfvi_payload = [
    {
        "ns_name": "sky_balls",
        "vnf_name": "faas_vtranscoder_2_7_2_edge1_vnfd",
        "vnf_index": "1",
        "invoker-selector": "cpu",
        "action_params": {
            "produce_profiles": [1]
        }
    },
    {
        "ns_name": "sky_balls",
        "vnf_name": "faas_vtranscoder_2_7_2_edge1_vnfd",
        "vnf_index": "2",
        "invoker-selector": "cpu"
    }
]

KEY = "faas"


def main():
    """Main process"""
    kafka_producer = init_producer()
    for action in day_1_payload + day_1_nfvi_payload:
        t = kafka_producer.send(KAFKA_CONFIGURATION_TOPIC, value=action, key=KEY)
        try:
            t.get(timeout=5)
        except KafkaError as e:
            pass
    kafka_producer.close()


if __name__ == '__main__':
    main()
