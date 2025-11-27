#!/bin/bash

echo "🔧 Setup Demo 06 - Kafka Connect JDBC Sink"
echo ""

# 1. Criar tópico
echo "1️⃣  Criando tópico 'demo-orders'..."
docker exec kafka kafka-topics --create \
    --topic demo-orders \
    --bootstrap-server kafka:29092 \
    --partitions 3 \
    --replication-factor 1 2>/dev/null || echo "   ⚠️  Tópico já existe"

echo ""

# 2. Aguardar Kafka Connect estar pronto
echo "2️⃣  Aguardando Kafka Connect inicializar..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8083/ > /dev/null 2>&1; then
        echo "   ✅ Kafka Connect está pronto!"
        break
    fi
    attempt=$((attempt + 1))
    echo "   ⏳ Tentativa $attempt/$max_attempts..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "   ❌ Timeout aguardando Kafka Connect"
    exit 1
fi

echo ""

# 3. Registrar conector
echo "3️⃣  Registrando JDBC Sink Connector..."
curl -X POST http://localhost:8083/connectors \
    -H "Content-Type: application/json" \
    -d @connector-config.json

echo ""
echo ""

# 4. Verificar status
echo "4️⃣  Status do conector:"
sleep 2
curl -s http://localhost:8083/connectors/jdbc-sink-orders-demo/status | python3 -m json.tool

echo ""
echo "✅ Setup concluído!"
echo ""
echo "📝 Próximos passos:"
echo "   - Execute: python order_generator.py"
echo "   - Verifique os dados: bash verify.sh"


