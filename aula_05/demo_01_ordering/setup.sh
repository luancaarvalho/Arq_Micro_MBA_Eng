#!/bin/bash

set -euo pipefail

TOPIC="ordering.transactions"

echo "🔧 Criando tópico '${TOPIC}' (RF=3, partitions=3)..."

docker exec kafka kafka-topics \
  --create \
  --topic "${TOPIC}" \
  --bootstrap-server kafka:29092 \
  --partitions 3 \
  --replication-factor 3 2>/dev/null && CREATED=1 || CREATED=0

if [ $CREATED -eq 1 ]; then
  echo "✅ Tópico criado"
else
  echo "ℹ️  Tópico já existe"
fi
