#!/bin/bash
echo "Criando tópico 'demo_producers' com alta disponibilidade..."
docker exec kafka kafka-topics --create \
    --topic demo_producers \
    --bootstrap-server kafka:29092 \
    --partitions 3 \
    --replication-factor 3 \
    --config min.insync.replicas=2

echo "Tópico criado!"
echo "Detalhes (Observe a lista de 'Replicas' e 'ISR'):"
docker exec kafka kafka-topics --describe \
    --topic demo_producers \
    --bootstrap-server kafka:29092

