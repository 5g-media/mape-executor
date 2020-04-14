import os

DEBUG = int(os.environ.get("DEBUG", 1))
PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))

# =================================
# KAFKA SETTINGS
# =================================
KAFKA_SERVER = "{}:{}".format(os.environ.get("KAFKA_HOST", "217.172.11.173"),
                              os.environ.get("KAFKA_PORT", "9092"))
KAFKA_CLIENT_ID = 'actions-execution-engine'
KAFKA_API_VERSION = (1, 1, 0)
KAFKA_EXECUTION_TOPIC = os.environ.get("KAFKA_EXECUTION_TOPIC", "ns.instances.exec")
KAFKA_CONFIGURATION_TOPIC = os.environ.get("KAFKA_CONFIGURATION_TOPIC", "ns.instances.conf")
KAFKA_SPECTATOR_CONFIGURATION_TOPIC = os.environ.get("KAFKA_SPECTATOR_CONFIGURATION_TOPIC",
                                                     "spectators.vtranscoder3d.conf")
# Use unique consumer group per UC
KAFKA_GROUP_ID = {"worker": "MAPE_ACTIONS_CG", "osm_kafka_subscriber": "5GMEDIA_EXECUTION_CG"}

# =================================
# OSM SETTINGS
# =================================
OSM_IP = os.environ.get("OSM_IP", '217.172.11.180')  # '217.172.11.188'
OSM_FAAS_IP = OSM_IP
OSM_FAAS_PORT = '5001'
OSM_ADMIN_CREDENTIALS = {"username": os.environ.get("OSM_USER", "admin"),
                         "password": os.environ.get("OSM_PWD", "admin")}
OSM_COMPONENTS = {"UI": 'http://{}:80'.format(OSM_IP),
                  "NBI-API": 'https://{}:9999'.format(OSM_IP),
                  "RO-API": 'http://{}:9090'.format(OSM_IP)}
OSM_KAFKA_SERVER = "{}:{}".format(OSM_IP, os.environ.get("OSM_KAFKA_PORT", "9094"))
OSM_KAFKA_NS_TOPIC = 'ns'

# =================================
# UC3
# =================================
vCDN_NSD_PREFIX = 'faas_vm_vCDN'
VDNS_IP = os.environ.get("VDNS_IP", '192.168.111.20')
VDNS_PORT = '9999'

# =================================
# INFLUXDB SETTINGS
# =================================
# See InfluxDBClient class
INFLUX_DATABASES = {
    'default': {
        'ENGINE': 'influxdb',
        'NAME': os.environ.get("INFLUXDB_DB_NAME", 'monitoring'),
        'USERNAME': os.environ.get("INFLUXDB_USER", 'root'),
        'PASSWORD': os.environ.get("INFLUXDB_PWD", 'root'),
        'HOST': os.environ.get("INFLUXDB_IP", "217.172.11.173"),
        'PORT': os.environ.get("INFLUXDB_PORT", 8086)
    }
}

# =================================
# GRAYLOG SETTINGS
# =================================
GRAYLOG_HOST = os.environ.get("GRAYLOG_HOST", '192.168.1.175')
GRAYLOG_PORT = os.environ.get("GRAYLOG_PORT", 12201)

# ==================================
# LOGGING SETTINGS
# ==================================
# See more: https://docs.python.org/3.5/library/logging.config.html
DEFAULT_HANDLER_SETTINGS = {
    'class': 'logging.handlers.RotatingFileHandler',
    'filename': "{}/logs/worker.log".format(PROJECT_ROOT),
    'mode': 'w',
    'formatter': 'detailed',
    'level': 'INFO',
    'maxBytes': 4096 * 4096,
    'backupCount': 20,
}

# DEFAULT_HANDLER_SETTINGS = {
#     'class': 'graypy.GELFUDPHandler',
#     'formatter': 'detailed',
#     'level': 'DEBUG' if DEBUG else 'WARNING',
#     'host': GRAYLOG_HOST,
#     'port': GRAYLOG_PORT
# }

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'detailed': {
            'class': 'logging.Formatter',
            'format': "[%(asctime)s] - [%(name)s:%(lineno)s] - [%(levelname)s] %(message)s",
        },
        'simple': {
            'class': 'logging.Formatter',
            'format': '%(name)-15s %(levelname)-8s %(processName)-10s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'simple',
        },
        'graylog': DEFAULT_HANDLER_SETTINGS,
        'worker': DEFAULT_HANDLER_SETTINGS,
        'osm_kafka_subscriber': DEFAULT_HANDLER_SETTINGS,
        'osm': {
            'class': 'graypy.GELFUDPHandler',
            'formatter': 'detailed',
            'level': 'DEBUG' if DEBUG else 'INFO',
            'host': GRAYLOG_HOST,
            'port': GRAYLOG_PORT
        },
    },
    'loggers': {
        'worker': {
            'handlers': ['worker']
        },
        'osm_kafka_subscriber': {
            'handlers': ['osm_kafka_subscriber']
        },
        'osm': {
            'handlers': ['osm']
        }
    }
}
