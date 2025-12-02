#!/bin/bash

echo "⏳ Aguardando Kafka Connect ficar disponível..."
sleep 10

echo "🚀 Criando connector Debezium..."
curl -X POST http://kafka-connect:8083/connectors \
  -H "Content-Type: application/json" \
  -d @/kafka-connect-init/connector.json
