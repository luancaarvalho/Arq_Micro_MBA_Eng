#!/bin/bash

echo "Aguardando Kafka Connect ficar disponivel..."
sleep 10

echo "Criando connector Debezium..."
curl -X POST http://connect:8083/connectors \
  -H "Content-Type: application/json" \
  -d @/connectors/connector.json
