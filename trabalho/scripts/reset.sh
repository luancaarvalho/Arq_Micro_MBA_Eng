#!/bin/bash

set -e

# Detectar o diretรณrio do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "============================================================"
echo -e "${RED} RESET COMPLETO DO PIPELINE CDC ${NC}"
echo "============================================================"
echo ""
echo "Este script irรก:"
echo "  โ€ข Parar o consumidor Python (Kafka โ’ MinIO)"
echo "  โ€ข Remover conectores Kafka Connect"
echo "  โ€ข Derrubar containers Docker"
echo "  โ€ข Remover volumes (Postgres, Kafka, MinIO)"
echo "  โ€ข Limpar logs locais (.logs)"
echo ""
echo -e "${RED}ATENรรO: TODOS os dados serรฃo apagados!${NC}"
echo ""

read -p "Confirmar reset? (sim/nรฃo): " confirm

if [[ "$confirm" != "sim" && "$confirm" != "s" && "$confirm" != "y" ]]; then
    echo -e "${YELLOW}Reset cancelado.${NC}"
    exit 0
fi

cd "$WORK_DIR"

echo ""
echo -e "${YELLOW}๐”น Parando consumidor Python...${NC}"
if pgrep -f kafka_to_minio.py > /dev/null 2>&1; then
    pkill -f kafka_to_minio.py
    echo -e "${GREEN}โ” Consumidor parado${NC}"
else
    echo "   Consumidor nรฃo estava rodando"
fi

echo ""
echo -e "${YELLOW}๐”น Removendo conectores Kafka Connect...${NC}"

CONNECTORS=("debezium-postgres-source" "jdbc-sink-postgres")

for c in "${CONNECTORS[@]}"; do
    if curl -s "http://localhost:8083/connectors/$c" >/dev/null 2>&1; then
        curl -s -X DELETE "http://localhost:8083/connectors/$c" >/dev/null 2>&1 || true
        echo "   โ” Conector removido: $c"
    else
        echo "   (Nรฃo encontrado): $c"
    fi
done

echo ""
echo -e "${YELLOW}๐”น Derrubando containers Docker...${NC}"
docker compose down || echo "Containers jรก estavam parados"

echo ""
echo -e "${YELLOW}๐”น Removendo volumes Docker...${NC}"
docker compose down -v || true
echo -e "${GREEN}โ” Volumes removidos${NC}"

echo ""
echo -e "${YELLOW}๐”น Limpando logs locais...${NC}"
if [ -d "$WORK_DIR/.logs" ]; then
    rm -rf "$WORK_DIR/.logs"
    echo -e "${GREEN}โ” Logs apagados${NC}"
else
    echo "   Nenhum log encontrado"
fi

echo ""
echo "============================================================"
echo -e "${GREEN} RESET CONCLUรDO COM SUCESSO! ${NC}"
echo "============================================================"

echo ""
echo -e "${BLUE}Para reiniciar o pipeline:${NC}"
echo ""
echo "  docker compose up -d"
echo "  python scripts/setup.py"
echo "  python scripts/initial_load.py"
echo "  python scripts/mutations.py"
echo "  python scripts/validate.py"
echo ""