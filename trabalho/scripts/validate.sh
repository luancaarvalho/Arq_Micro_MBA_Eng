#!/usr/bin/env bash
set -euo pipefail

# Compact validation script for the CDC pipeline
# Checks: source vs sink counts, MinIO objects, connector states

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "============================================================"
echo "VALIDAÇÃO DO PIPELINE CDC"
echo "============================================================"
echo

execute_query() {
    local container_suffix=$1
    local db=$2
    local query=$3
    docker exec -i postgres-$container_suffix psql -U postgres -d $db -t -A -c "$query" 2>&1 || true
}

echo -e "${BLUE}1) PostgreSQL Sink${NC}"
if docker exec postgres-sink pg_isready -U postgres -d sink_db >/dev/null 2>&1; then
    echo -e "   ${GREEN}postgres-sink ready${NC}"
else
    echo -e "   ${YELLOW}postgres-sink not ready${NC}"
fi

count_sink=$(execute_query "sink" "sink_db" "SELECT COUNT(*) FROM products;")
count_sink=$(echo "$count_sink" | tr -d '\r' | tr -d '\n' | tr -d '[:space:]')

if [ -z "$count_sink" ] || [ "$count_sink" = "0" ]; then
    echo -e "   ${RED}Nenhum produto encontrado no PostgreSQL Sink${NC}"
else
    echo -e "   ${GREEN}Total produtos no sink: $count_sink${NC}"
fi

echo
echo -e "${BLUE}2) Comparação Fonte vs Sink${NC}"
count_source=$(execute_query "source" "source_db" "SELECT COUNT(*) FROM products;" 2>/dev/null | tr -d ' ')
echo "   Fonte: $count_source  |  Sink: $count_sink"
if [ "$count_source" = "$count_sink" ] && [ "$count_sink" -gt 0 ]; then
    echo -e "   ${GREEN}Contagens coincidem${NC}"
else
    echo -e "   ${YELLOW}Contagens distintas — investigar logs/conectores${NC}"
fi

echo
echo -e "${BLUE}3) MinIO${NC}"
file_count=0
if docker ps --filter "name=minio" --filter "status=running" -q >/dev/null 2>&1; then
    docker exec minio mc alias set local http://localhost:9000 minioadmin minioadmin >/dev/null 2>&1 || true
    file_count=$(docker exec minio mc ls local/cdc-data --recursive 2>/dev/null | wc -l | tr -d ' ')
else
    if command -v mc >/dev/null 2>&1; then
        mc alias set local http://localhost:9000 minioadmin minioadmin >/dev/null 2>&1 || true
        file_count=$(mc ls local/cdc-data --recursive 2>/dev/null | wc -l | tr -d ' ')
    else
        echo -e "   ${YELLOW}Não foi possível checar MinIO (cliente 'mc' ausente e container MinIO não encontrado)${NC}"
        file_count=0
    fi
fi

if [ -z "$file_count" ] || [ "$file_count" = "0" ]; then
    echo -e "   ${YELLOW}Nenhum arquivo em MinIO detectado${NC}"
else
    echo -e "   ${GREEN}Arquivos em MinIO: $file_count${NC}"
fi

echo
echo -e "${BLUE}4) Status dos conectores${NC}"
for name in debezium-postgres-source jdbc-sink-postgres; do
    status=$(curl -sSf http://localhost:8083/connectors/$name/status 2>/dev/null | jq -r '.connector.state' 2>/dev/null || echo "UNKNOWN")
    if [ "$status" = "RUNNING" ]; then
        echo -e "   ${GREEN}$name: $status${NC}"
    else
        echo -e "   ${RED}$name: $status${NC}"
    fi
done

echo
echo "Resumo:"
if [ "$count_source" = "$count_sink" ] && [ "$count_sink" -gt 0 ]; then
    echo -e "   ${GREEN}Pipeline CDC aparenta estar funcionando${NC}"
else
    echo -e "   ${RED}Pipeline CDC com diferenças — verifique logs e conectores${NC}"
fi

echo
echo "Dicas de depuração:"
echo "  - Ver logs: docker logs kafka-connect"
echo "  - Ver Debezium logs: docker logs kafka-connect | grep debezium"
echo "  - Ver arquivos MinIO: docker exec minio mc ls local/cdc-data --recursive | head -n 20"
