#!/bin/bash

set -e

# Detectar o diretório do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CONNECTORS_DIR="$WORK_DIR/connectors"

echo " Setup Pipeline CDC - Iniciando configuração..."
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Aguardar serviços estarem prontos
echo -e "${YELLOW}  Aguardando serviços estarem prontos...${NC}"
echo "   Aguardando PostgreSQL fonte..."
until docker exec postgres-source pg_isready -U postgres > /dev/null 2>&1; do
    echo "    PostgreSQL fonte ainda não está pronto..."
    sleep 2
done
echo -e "   ${GREEN} PostgreSQL fonte pronto!${NC}"

echo "   Aguardando PostgreSQL destino..."
until docker exec postgres-sink pg_isready -U postgres > /dev/null 2>&1; do
    echo "    PostgreSQL destino ainda não está pronto..."
    sleep 2
done
echo -e "   ${GREEN} PostgreSQL destino pronto!${NC}"

echo "   Aguardando Kafka Connect..."
max_attempts=60
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8083/ > /dev/null 2>&1; then
        echo -e "   ${GREEN} Kafka Connect está pronto!${NC}"
        break
    fi
    attempt=$((attempt + 1))
    if [ $((attempt % 5)) -eq 0 ]; then
        echo "    Tentativa $attempt/$max_attempts..."
    fi
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "   ${RED} Timeout aguardando Kafka Connect${NC}"
    exit 1
fi

echo ""

# 2. Criar tabela no PostgreSQL fonte
echo -e "${YELLOW}  Criando tabela 'products' no PostgreSQL fonte...${NC}"

# Aguardar PostgreSQL estar realmente pronto para aceitar queries
sleep 3

# Criar tabela usando arquivo SQL temporário
cat > /tmp/create_table.sql <<'EOSQL'
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    category VARCHAR(100),
    stock INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_products_updated_at ON products;
CREATE TRIGGER update_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
EOSQL

docker exec -i postgres-source psql -U postgres -d source_db < /tmp/create_table.sql > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "   ${GREEN} Tabela 'products' criada!${NC}"
    rm -f /tmp/create_table.sql
else
    echo -e "   ${RED} Erro ao criar tabela${NC}"
    cat /tmp/create_table.sql
    rm -f /tmp/create_table.sql
    exit 1
fi
echo ""

echo -e "${YELLOW}  Configurando MinIO...${NC}"
echo "   Aguardando MinIO estar pronto..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker ps --filter "name=minio" --filter "status=running" -q > /dev/null 2>&1; then
        if docker exec minio mc alias set local http://localhost:9000 minioadmin minioadmin > /dev/null 2>&1; then
            echo -e "   ${GREEN} MinIO (container) está pronto!${NC}"
            minio_mode="container"
            break
        fi
    else
        if command -v mc >/dev/null 2>&1; then
            if mc alias set local http://localhost:9000 minioadmin minioadmin > /dev/null 2>&1; then
                echo -e "   ${GREEN} MinIO (host) está pronto!${NC}"
                minio_mode="host"
                break
            fi
        fi
    fi
    attempt=$((attempt + 1))
    if [ $((attempt % 5)) -eq 0 ]; then
        echo "    Tentativa $attempt/$max_attempts..."
    fi
    sleep 2
done

if [ $attempt -lt $max_attempts ]; then
    # Criar bucket usando método apropriado
    if [ "${minio_mode}" = "container" ]; then
        docker exec minio mc mb local/cdc-data 2>/dev/null || echo "   Bucket já existe"
        docker exec minio mc anonymous set download local/cdc-data 2>/dev/null || true
        echo -e "   ${GREEN} MinIO (container) configurado!${NC}"
    else
        if command -v mc >/dev/null 2>&1; then
            mc mb local/cdc-data 2>/dev/null || echo "   Bucket já existe"
            mc anonymous set download local/cdc-data 2>/dev/null || true
            echo -e "   ${GREEN} MinIO (host) configurado!${NC}"
        else
            echo -e "   ${YELLOW}  Não foi possível configurar bucket: 'mc' não encontrado no host${NC}"
            echo "   Instale o cliente 'mc' (https://min.io/docs/minio/linux/reference/minio-mc.html) ou rode o MinIO como container"
        fi
    fi
else
    echo -e "   ${RED} Timeout aguardando MinIO${NC}"
fi
echo ""

# 4. Verificar Schema Registry
echo -e "${YELLOW}  Verificando Schema Registry...${NC}"
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    schema_registry_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8082/subjects 2>/dev/null)
    if [ "$schema_registry_response" = "200" ] || [ "$schema_registry_response" = "000" ]; then
        if [ "$schema_registry_response" = "200" ]; then
            echo -e "   ${GREEN} Schema Registry está pronto!${NC}"
            break
        fi
    fi
    attempt=$((attempt + 1))
    if [ $((attempt % 5)) -eq 0 ]; then
        echo "    Tentativa $attempt/$max_attempts..."
    fi
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "   ${YELLOW}⚠️  Schema Registry pode não estar acessível, mas continuando...${NC}"
    echo "   Verifique se o Schema Registry está rodando: docker ps | grep schema-registry"
fi
echo ""

# 5. Verificar conectividade do Kafka Connect com Schema Registry
echo -e "${YELLOW}  Verificando conectividade Kafka Connect → Schema Registry...${NC}"
schema_test=$(docker exec kafka-connect curl -s -o /dev/null -w "%{http_code}" http://schema-registry:8081/subjects 2>/dev/null || echo "000")
if [ "$schema_test" = "200" ]; then
    echo -e "   ${GREEN} Kafka Connect consegue acessar Schema Registry!${NC}"
else
    echo -e "   ${YELLOW}  Kafka Connect pode não conseguir acessar Schema Registry${NC}"
    echo "   Isso pode causar erros ao registrar conectores com Avro"
fi
echo ""

# 6. Registrar conectores
register_connector() {
    local config_file=$1
    local connector_name=$(basename "$config_file" .json)    # Verificar se o arquivo existe
    if [ ! -f "$config_file" ]; then
        echo -e "   ${RED} Arquivo não encontrado: $config_file${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}   Registrando $connector_name...${NC}"
    
    # Verificar se o conector já existe
    status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8083/connectors/$connector_name)
    
    if [ "$status" = "200" ]; then
        echo -e "   ${YELLOW}  Conector já existe, deletando...${NC}"
        curl -s -X DELETE http://localhost:8083/connectors/$connector_name > /dev/null
        sleep 2
    fi
    
    # Registrar o conector - ler arquivo e enviar conteúdo
    if [ ! -r "$config_file" ]; then
        echo -e "   ${RED} Não é possível ler o arquivo: $config_file${NC}"
        return 1
    fi
    
    # Validar JSON antes de enviar
    if ! python3 -m json.tool "$config_file" > /dev/null 2>&1; then
        echo -e "   ${RED} Arquivo JSON inválido: $config_file${NC}"
        return 1
    fi
    
    # Enviar o conteúdo do arquivo
    response=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8083/connectors \
        -H "Content-Type: application/json" \
        --data-binary @"$config_file" 2>&1)
    
    http_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "201" ]; then
        echo -e "   ${GREEN} Conector registrado com sucesso!${NC}"
    elif [ "$http_code" = "409" ]; then
        echo -e "   ${YELLOW}  Conector já existe${NC}"
    else
        echo -e "   ${RED} Falha ao registrar (HTTP ${http_code})${NC}"
        if [ ! -z "$response_body" ]; then
            echo "   Resposta do servidor:"
            echo "$response_body" | python3 -m json.tool 2>/dev/null || echo "$response_body"
        fi
        echo "   Arquivo de configuração: $config_file"
        return 1
    fi
    
    sleep 3
}

echo -e "${YELLOW}  Registrando conectores...${NC}"

# Verificar se os arquivos de configuração existem
if [ ! -f "$CONNECTORS_DIR/debezium-source.json" ]; then
    echo -e "   ${RED} Arquivo $CONNECTORS_DIR/debezium-source.json não encontrado!${NC}"
    echo "   Diretório atual: $(pwd)"
    echo "   CONNECTORS_DIR: $CONNECTORS_DIR"
    exit 1
fi

# Registrar Debezium source primeiro
register_connector "$CONNECTORS_DIR/debezium-source.json"

# Aguardar um pouco para o Debezium criar o slot de replicação
echo "   Aguardando Debezium criar slot de replicação..."
sleep 10

# Registrar sinks
register_connector "$CONNECTORS_DIR/jdbc-sink-postgres.json"

echo ""
# 7. Verificar status dos conectores (Debezium e JDBC)
echo -e "${YELLOW}  Verificando status dos conectores...${NC}"
sleep 5

check_connector_status() {
    local connector_name=$1
    status=$(curl -s http://localhost:8083/connectors/$connector_name/status | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('connector',{}).get('state','UNKNOWN'))" 2>/dev/null || echo "UNKNOWN")
    echo "   $connector_name: $status"
}

check_connector_status "debezium-postgres-source"
check_connector_status "jdbc-sink-postgres"

# Iniciar o consumidor Python que grava em MinIO (fallback) — garantimos que exista apenas uma instância
echo ""
echo -e "   ${YELLOW}  Iniciando consumidor Python para MinIO (persistência de eventos)${NC}"
mkdir -p "$WORK_DIR/.logs"
if command -v python3 >/dev/null 2>&1; then
    if pgrep -f kafka_to_minio.py >/dev/null 2>&1; then
        echo "     Consumidor Python já em execução"
    else
        nohup python3 "$WORK_DIR/scripts/kafka_to_minio.py" > "$WORK_DIR/.logs/kafka_to_minio.log" 2>&1 &
        echo "    Consumidor Python iniciado (log: $WORK_DIR/.logs/kafka_to_minio.log)"
    fi
else
    echo "   ${RED} python3 não encontrado; não foi possível iniciar consumidor MinIO${NC}"
fi

echo ""
echo -e "${GREEN} Setup concluído com sucesso!${NC}"
echo ""
echo "   Próximos passos:"
echo "   1. Execute: python scripts/initial_load.py"
echo "   2. Execute: python scripts/mutations.py"
echo "   3. Valide os dados: bash scripts/validate.sh"

