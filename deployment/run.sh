#!/bin/bash

sed -i "s/ENV_DEBUG/$DEBUG/g" /etc/supervisor/supervisord.conf
sed -i "s/ENV_KAFKA_HOST/$KAFKA_HOST/g" /etc/supervisor/supervisord.conf
sed -i "s/ENV_KAFKA_PORT/$KAFKA_PORT/g" /etc/supervisor/supervisord.conf
sed -i "s/ENV_KAFKA_EXECUTION_TOPIC/$KAFKA_EXECUTION_TOPIC/g" /etc/supervisor/supervisord.conf
sed -i "s/ENV_KAFKA_CONFIGURATION_TOPIC/$KAFKA_CONFIGURATION_TOPIC/g" /etc/supervisor/supervisord.conf
sed -i "s/ENV_KAFKA_SPECTATOR_CONFIGURATION_TOPIC/$KAFKA_SPECTATOR_CONFIGURATION_TOPIC/g" /etc/supervisor/supervisord.conf
sed -i "s/ENV_OSM_IP/$OSM_IP/g" /etc/supervisor/supervisord.conf
sed -i "s/ENV_OSM_USER/$OSM_USER/g" /etc/supervisor/supervisord.conf
sed -i "s/ENV_OSM_PWD/$OSM_PWD/g" /etc/supervisor/supervisord.conf
sed -i "s/ENV_OSM_KAFKA_PORT/$OSM_KAFKA_PORT/g" /etc/supervisor/supervisord.conf
sed -i "s/ENV_VDNS_IP/$VDNS_IP/g" /etc/supervisor/supervisord.conf
sed -i "s/ENV_INFLUXDB_IP/$INFLUXDB_IP/g" /etc/supervisor/supervisord.conf
sed -i "s/ENV_INFLUXDB_DB_NAME/$INFLUXDB_DB_NAME/g" /etc/supervisor/supervisord.conf
sed -i "s/ENV_INFLUXDB_USER/$INFLUXDB_USER/g" /etc/supervisor/supervisord.conf
sed -i "s/ENV_INFLUXDB_PWD/$INFLUXDB_PWD/g" /etc/supervisor/supervisord.conf
sed -i "s/ENV_INFLUXDB_PORT/$INFLUXDB_PORT/g" /etc/supervisor/supervisord.conf
sed -i "s/ENV_GRAYLOG_HOST/$GRAYLOG_HOST/g" /etc/supervisor/supervisord.conf
sed -i "s/ENV_GRAYLOG_PORT/$GRAYLOG_PORT/g" /etc/supervisor/supervisord.conf

# Restart services
service supervisor start && service supervisor status

# Makes services start on system start
update-rc.d supervisor defaults

echo "Initialization completed."
tail -f /dev/null  # Necessary in order for the container to not stop
