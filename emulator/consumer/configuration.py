import json
from emulator.utils import init_consumer
from settings import KAFKA_CONFIGURATION_TOPIC


def main():
    kafka_consumer = init_consumer("TEST_CONF_SUBSCRIBER1")
    kafka_consumer.subscribe(pattern=KAFKA_CONFIGURATION_TOPIC)

    for msg in kafka_consumer:
        topic = msg.topic
        try:
            key = msg.key.decode('utf-8')
            value = json.loads(msg.value.decode('utf-8'))
            print("[Topic {}] key: {} has value {}".format(topic, key, value))
        except AttributeError as e:
            print("{}".format(e))
        except json.decoder.JSONDecodeError:
            print("Invalid message")
        except Exception as e:
            print("{}".format(e))
            pass


if __name__ == '__main__':
    main()
