#!/bin/bash

set -e

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=" | head -c 60
echo ""
echo "VALIDAÇÃO DO PIPELINE CDC"
echo "=" | head -c 60
echo ""
echo "Este script valida se os dados foram replicados corretamente"
echo "nos destinos: PostgreSQL Sink e MinIO (S3)"
echo ""

# Função para executar query no PostgreSQL
execute_query() {
    local host=$1
    local port=$2
    local db=$3
    local query=$4
    # Use -t -A to return unaligned tuples only; capture both stdout and stderr
    docker exec -i postgres-$host psql -U postgres -d $db -t -A -c "$query" 2>&1 || true
}

# 1. Validar PostgreSQL Sink
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}1️⃣  VALIDAÇÃO: PostgreSQL SINK${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Checar se o container postgres-sink responde
echo -n "Checking postgres-sink readiness... "
if docker exec postgres-sink pg_isready -U postgres -d sink_db >/dev/null 2>&1; then
    echo -e "${GREEN}ready${NC}"
else
    echo -e "${YELLOW}not ready${NC} (container may be starting or unavailable)"
fi

# Contar produtos no sink (captura stdout/stderr para diagnóstico)
count_sink_output=$(execute_query "sink" "5432" "sink_db" "SELECT COUNT(*) FROM products;" )
# normalize whitespace and newlines to a single trimmed number
count_sink=$(echo "$count_sink_output" | tr -d '\r' | tr -d '\n' | tr -d '[:space:]')

if [ -z "$count_sink" ] || [ "$count_sink" = "0" ]; then
    echo -e "${RED}❌ Nenhum produto encontrado no PostgreSQL Sink${NC}"
    echo "   Verifique se o conector JDBC Sink está funcionando"
    if [ -n "$count_sink_output" ]; then
        echo "--- psql output (diagnóstico) ---"
        echo "$count_sink_output"
        echo "--- fim do diagnóstico ---"
    fi
else
    echo -e "${GREEN}✅ Total de produtos no PostgreSQL Sink: $count_sink${NC}"
fi

echo ""
echo "📋 Listando produtos no PostgreSQL Sink:"
echo ""

products_output=$(execute_query "sink" "5432" "sink_db" "SELECT id||'|'||coalesce(name,'')||'|'||coalesce(price::text,'')||'|'||coalesce(stock::text,'')||'|'||coalesce(category,'')||'|'||coalesce(TO_CHAR(updated_at, 'YYYY-MM-DD HH24:MI:SS'),'') as line FROM products ORDER BY id;" )

if [ -z "$products_output" ]; then
    echo "   (nenhum dado retornado na listagem)"
else
    echo "$products_output" | while IFS='|' read -r id name price stock category updated_at; do
        if [ ! -z "$id" ]; then
            printf "   ID: %-3s | %-35s | R$ %8s | Estoque: %3s | %s\n" \
                "$id" "$name" "$price" "$stock" "$category"
        fi
    done
fi

echo ""

# 2. Comparar contagens entre fonte e sink
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}2️⃣  COMPARAÇÃO: Fonte vs Sink${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

count_source=$(execute_query "source" "5432" "source_db" "SELECT COUNT(*) FROM products;" 2>/dev/null | tr -d ' ')

echo "   PostgreSQL Fonte: $count_source produtos"
echo "   PostgreSQL Sink:  $count_sink produtos"

if [ "$count_source" = "$count_sink" ]; then
    echo -e "   ${GREEN}✅ Contagens coincidem!${NC}"
else
    echo -e "   ${RED}❌ Contagens não coincidem!${NC}"
    echo "   Diferença: $((count_source - count_sink)) produtos"
fi

echo ""

# 3. Validar MinIO (S3)
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}3️⃣  VALIDAÇÃO: MinIO (S3)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Verificar se o bucket existe e tem arquivos
docker exec minio mc alias set local http://localhost:9000 minioadmin minioadmin > /dev/null 2>&1

file_count=$(docker exec minio mc ls local/cdc-data --recursive 2>/dev/null | wc -l | tr -d ' ')

if [ "$file_count" = "0" ]; then
    echo -e "${YELLOW}⚠️  Nenhum arquivo encontrado no MinIO ainda${NC}"
    echo "   Isso é normal se o S3 Sink Connector ainda não processou dados"
    echo "   ou se o flush.size ainda não foi atingido"
else
    echo -e "${GREEN}✅ Arquivos encontrados no MinIO: $file_count${NC}"
    echo ""
    echo "📁 Estrutura de diretórios no bucket 'cdc-data':"
    docker exec minio mc ls local/cdc-data --recursive 2>/dev/null | head -10
    if [ "$file_count" -gt 10 ]; then
        echo "   ... (mostrando apenas os 10 primeiros)"
    fi
fi

echo ""

# 4. Verificar status dos conectores
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}4️⃣  STATUS DOS CONECTORES${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

check_connector() {
    local name=$1
    # Use curl -fs to fail on non-2xx and parse with jq; fallback to UNKNOWN
    local status=$(curl -sSf http://localhost:8083/connectors/$name/status 2>/dev/null | jq -r '.connector.state' 2>/dev/null || echo "UNKNOWN")

    if [ "$status" = "RUNNING" ]; then
        echo -e "   ${GREEN}✅ $name: $status${NC}"
    else
        echo -e "   ${RED}❌ $name: $status${NC}"
    fi
}

check_connector "debezium-postgres-source"
check_connector "jdbc-sink-postgres"
check_connector "s3-sink-minio"

echo ""

# 5. Verificar tópicos Kafka
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}5️⃣  TÓPICOS KAFKA${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

topic_name="cdc-source-server.public.products"
topic_info=$(docker exec kafka kafka-topics --describe \
    --topic "$topic_name" \
    --bootstrap-server kafka:29092 2>/dev/null || echo "")

if [ -z "$topic_info" ]; then
    echo -e "${YELLOW}⚠️  Tópico '$topic_name' não encontrado${NC}"
else
    echo -e "${GREEN}✅ Tópico encontrado: $topic_name${NC}"
    echo ""
    echo "$topic_info" | head -3
fi

echo ""

# Resumo final
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}📊 RESUMO DA VALIDAÇÃO${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ "$count_source" = "$count_sink" ] && [ "$count_sink" -gt 0 ]; then
    echo -e "${GREEN}✅ Pipeline CDC funcionando corretamente!${NC}"
    echo "   - Dados replicados do PostgreSQL fonte para o sink"
    echo "   - Conectores em execução"
else
    echo -e "${RED}❌ Pipeline CDC com problemas${NC}"
    echo "   - Verifique os logs dos conectores"
    echo "   - Execute: docker logs kafka-connect"
fi

echo ""
echo "💡 Para ver logs detalhados:"
echo "   - Debezium: docker logs kafka-connect | grep debezium"
echo "   - JDBC Sink: docker logs kafka-connect | grep jdbc"
echo "   - S3 Sink: docker logs kafka-connect | grep s3"

