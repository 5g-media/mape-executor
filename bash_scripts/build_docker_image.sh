#!/bin/bash

find ./actions-execution-engine -type d -exec sudo chmod -R 755 {} \;
find ./actions-execution-engine -type f -exec sudo chmod 664 {} \;
chmod a+x ./actions-execution-engine/deployment/run.sh ./actions-execution-engine/deployment/clean.sh
cp ./actions-execution-engine/deployment/Dockerfile .
sudo docker build -t actions-execution-engine .
source ./actions-execution-engine/deployment/clean.sh
