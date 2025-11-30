#!/bin/bash

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🔄 Reset do Pipeline CDC${NC}"
echo ""
echo "Este script irá:"
echo "  1. Parar todos os containers"
echo "  2. Remover containers e volumes"
echo "  3. Limpar dados (CUIDADO!)"
echo ""

read -p "Tem certeza que deseja continuar? (sim/não): " confirm

if [ "$confirm" != "sim" ] && [ "$confirm" != "s" ] && [ "$confirm" != "yes" ] && [ "$confirm" != "y" ]; then
    echo "Operação cancelada."
    exit 0
fi

echo ""
echo -e "${YELLOW}1️⃣  Parando containers...${NC}"
docker-compose down

echo ""
echo -e "${YELLOW}2️⃣  Removendo volumes...${NC}"
docker-compose down -v

echo ""
echo -e "${GREEN}✅ Reset concluído!${NC}"
echo ""
echo "Para reiniciar:"
echo "  1. docker-compose up -d"
echo "  2. bash scripts/setup.sh"

