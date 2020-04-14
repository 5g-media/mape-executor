#!/bin/bash

if sudo docker ps | grep -q 'mape-actions-execution'; then
    # Gracefully stop supervisor
    sudo docker exec -i mape-actions-execution service supervisor stop && \
    sudo docker stop mape-actions-execution && \
    sudo docker rm -f mape-actions-execution
fi