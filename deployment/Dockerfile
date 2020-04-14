FROM ubuntu:16.04
MAINTAINER Athanasoulis Panagiotis
LABEL version="1.0"

ENV DEBUG=$DEBUG
ENV KAFKA_HOST=$KAFKA_HOST
ENV KAFKA_PORT=$KAFKA_PORT
ENV KAFKA_EXECUTION_TOPIC=$KAFKA_EXECUTION_TOPIC
ENV KAFKA_CONFIGURATION_TOPIC=$KAFKA_CONFIGURATION_TOPIC
ENV KAFKA_SPECTATOR_CONFIGURATION_TOPIC=$KAFKA_SPECTATOR_CONFIGURATION_TOPIC
ENV OSM_IP=$OSM_IP
ENV OSM_USER=$OSM_USER
ENV OSM_PWD=$OSM_PWD
ENV OSM_KAFKA_PORT=$OSM_KAFKA_PORT
ENV VDNS_IP=$VDNS_IP
ENV INFLUXDB_IP=$INFLUXDB_IP
ENV INFLUXDB_DB_NAME=$INFLUXDB_DB_NAME
ENV INFLUXDB_USER=$INFLUXDB_USER
ENV INFLUXDB_PWD=$INFLUXDB_PWD
ENV INFLUXDB_PORT=$INFLUXDB_PORT
ENV GRAYLOG_HOST=$GRAYLOG_HOST
ENV GRAYLOG_PORT=$GRAYLOG_PORT

RUN pwd
RUN apt-get clean
RUN apt-get update

# Install required packages
RUN apt-get install -y iputils-ping --fix-missing
RUN which ping
RUN apt-get -y install build-essential apt-utils acl cron libxml2-dev python3-pip vim supervisor htop wget
RUN apt-get -y install python3-dev python3-lxml python3-cffi


# Copy source code
RUN mkdir /opt/actions-execution-engine
COPY actions-execution-engine /opt/actions-execution-engine
RUN ls -la /opt/actions-execution-engine
ADD actions-execution-engine/deployment/execution.conf /etc/supervisor/conf.d/execution.conf

RUN pip3 install -r /opt/actions-execution-engine/requirements.txt

# Configure Supervisor
RUN rm -rf /etc/supervisor/supervisord.conf && \
 cp /opt/actions-execution-engine/deployment/supervisor/supervisord.conf /etc/supervisor/supervisord.conf

EXPOSE 3333

# Run script
CMD bash /opt/actions-execution-engine/deployment/run.sh
