#!/bin/bash

set -e

# Detectar o diretório do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "============================================================"
echo -e "${RED}RESET COMPLETO DO PIPELINE CDC${NC}"
echo "============================================================"
echo ""
echo "Este script irá:"
echo "  1. Parar o consumidor Python (MinIO)"
echo "  2. Deletar conectores Kafka Connect"
echo "  3. Parar todos os containers"
echo "  4. Remover volumes (PostgreSQL, Kafka, MinIO)"
echo "  5. Limpar logs locais"
echo ""
echo -e "${RED} ATENÇÃO: Todos os dados serão perdidos!${NC}"
echo ""

read -p "Tem certeza que deseja continuar? (sim/não): " confirm

if [ "$confirm" != "sim" ] && [ "$confirm" != "s" ] && [ "$confirm" != "yes" ] && [ "$confirm" != "y" ]; then
    echo -e "${YELLOW}Operação cancelada.${NC}"
    exit 0
fi

cd "$WORK_DIR"

echo ""
echo -e "${YELLOW}  Parando consumidor Python...${NC}"
if pgrep -f kafka_to_minio.py >/dev/null 2>&1; then
    pkill -f kafka_to_minio.py
    echo -e "   ${GREEN} Consumidor Python parado${NC}"
else
    echo "     Consumidor Python não estava rodando"
fi

echo ""
echo -e "${YELLOW}  Deletando conectores Kafka Connect...${NC}"
for connector in debezium-postgres-source jdbc-sink-postgres; do
    if curl -s http://localhost:8083/connectors/$connector >/dev/null 2>&1; then
        curl -s -X DELETE http://localhost:8083/connectors/$connector >/dev/null 2>&1 || true
        echo "    Conector $connector deletado"
    else
        echo "     Conector $connector não encontrado"
    fi
done

echo ""
echo -e "${YELLOW}  Parando containers...${NC}"
docker-compose down 2>/dev/null || echo "    Containers já estavam parados"

echo ""
echo -e "${YELLOW}  Removendo volumes Docker...${NC}"
docker-compose down -v 2>/dev/null || true
echo -e "   ${GREEN} Volumes removidos${NC}"

echo ""
echo -e "${YELLOW}  Limpando logs locais...${NC}"
if [ -d "$WORK_DIR/.logs" ]; then
    rm -rf "$WORK_DIR/.logs"
    echo -e "   ${GREEN} Logs removidos${NC}"
else
    echo "    Sem logs para remover"
fi

echo ""
echo "============================================================"
echo -e "${GREEN} RESET CONCLUÍDO COM SUCESSO!${NC}"
echo "============================================================"
echo ""
echo -e "${BLUE} Próximos passos para reiniciar:${NC}"
echo ""
echo "     docker-compose up -d"
echo "     bash scripts/setup.sh"
echo "     python scripts/initial_load.py"
echo "     python scripts/mutations.py"
echo "     bash scripts/validate.sh"
echo ""

