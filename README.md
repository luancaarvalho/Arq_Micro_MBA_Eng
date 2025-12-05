### Projeto desemvolvido por:
## Nome / Matricula
* Marcos Aurelio Mendes Oliveira - 2519887
* Evellen Thais Gomes Silva - 2518889

# Pipeline CDC Fim a Fim

Pipeline completo de replicação de dados com Change Data Capture (CDC) usando Debezium, Kafka e múltiplos destinos.

## 📋 Arquitetura

```
Postgres Source → Debezium → Kafka → [Postgres Destination, MinIO]
```

### Componentes

- **Postgres Source**: Banco de dados fonte com replicação lógica habilitada (porta 5434)
- **Debezium**: Conector CDC que captura mudanças do Postgres
- **Kafka**: Message broker para distribuição de eventos
- **Schema Registry**: Gerenciamento de schemas
- **Kafka Connect**: Framework para conectar sistemas externos
- **Postgres Destination**: Banco de dados destino (porta 5433)
- **MinIO**: Armazenamento de objetos S3-compatible (porta 9000/9001)
- **Kafka UI**: Interface web para gerenciar Kafka (porta 8080)

## 🚀 Como Executar

### Pré-requisitos

- Docker e Docker Compose instalados
- Python 3.8+ com as dependências:
  ```bash
  pip install -r requirements.txt
  ```
  
  Ou instale manualmente:
  ```bash
  pip install psycopg[binary] kafka-python boto3
  ```

### Passo 1: Subir a Infraestrutura

```bash
docker compose up -d
```

Isso irá:
- Subir todos os serviços (Kafka, Postgres, MinIO, etc.)
- Aguardar o Kafka Connect ficar disponível
- Criar automaticamente o conector Debezium (via serviço `init-connector`)
- Inicializar as tabelas no banco fonte

**Nota:** O conector é criado automaticamente pelo serviço `init-connector` que aguarda o Kafka Connect estar saudável antes de executar.

### Passo 2: Configurar MinIO

1. Acesse o console do MinIO: http://localhost:9001
2. Login:
   - Username: `admin`
   - Password: `admin123`
3. Crie um bucket chamado `kafka-files`

### Passo 3: Executar Carga Inicial

```bash
python scripts/01_carga_inicial.py
```

Este script insere 10 registros de exemplo na tabela `users` do banco fonte.

### Passo 4: Iniciar os Consumers

Em terminais separados, execute os consumers:

**Consumer MinIO:**
```bash
python scripts/consumer_1_minio.py
```

**Consumer Postgres:**
```bash
python scripts/consumer_2_postgres.py
```

### Passo 5: Testar Mutações

Execute os scripts de mutação para demonstrar captura de INSERT, UPDATE e DELETE:

```bash
# INSERT
python scripts/02_mutacao_insert.py "Novo Usuario" "novo.usuario"

# UPDATE (substitua <id> por um ID válido)
python scripts/03_mutacao_update.py <id> "Nome Atualizado" "username.updated"

# DELETE (substitua <id> por um ID válido)
python scripts/04_mutacao_delete.py <id>
```

### Passo 6: Validar Resultados

```bash
python scripts/05_validacao.py
```

Este script mostra:
- Quantidade de registros no source e destination
- Arquivos no MinIO
- Comparação entre source e destination
- Sincronização dos dados

## 📁 Estrutura do Projeto

```
.
├── docker-compose.yaml          # Configuração de todos os serviços
├── connectors/                  # Configurações dos conectores
│   ├── connector.json          # Config do conector Debezium
│   └── README.md
├── scripts/                     # Scripts Python
│   ├── 01_carga_inicial.py     # Carga inicial de dados
│   ├── 02_mutacao_insert.py    # Teste de INSERT
│   ├── 03_mutacao_update.py    # Teste de UPDATE
│   ├── 04_mutacao_delete.py    # Teste de DELETE
│   ├── 05_validacao.py         # Validação dos destinos
│   ├── consultar_destination.py # Consulta dados no Postgres destino
│   ├── consumer_1_minio.py      # Consumer para MinIO
│   ├── consumer_2_postgres.py  # Consumer para Postgres
│   └── README.md
├── source/                     # Scripts SQL de inicialização
│   └── init.sql                # Criação da tabela users
├── kafka-connect-init/         # Scripts de inicialização (legado)
│   └── create-connector.sh     # Script de criação manual (não usado mais)
└── README.md                   # Este arquivo
```

## 🔍 Verificação e Validação

### Verificar Tópicos no Kafka

Acesse o Kafka UI: http://localhost:8080

Você deve ver o tópico: `pgserver.public.users`

### Verificar Conector

Execute no terminal/PowerShell:

```bash
curl http://localhost:8083/connectors/postgres-users-connector/status
```

### Consultar Dados no Postgres Destination

**Opção 1: Usando script Python (recomendado):**
```bash
python scripts/consultar_destination.py
```

**Opção 2: Usando Docker (se psql não estiver instalado):**
```bash
docker exec -it postgres_destination psql -U postgres -d destination_db -c "SELECT * FROM users;"
```

**Opção 3: Usando psql diretamente (se instalado):**
```bash
psql -h localhost -p 5433 -U postgres -d destination_db
```

```sql
SELECT * FROM users;
```

### Listar Arquivos no MinIO

Acesse o console do MinIO e navegue até o bucket `kafka-files`.

## 🛠️ Troubleshooting

### Conector não foi criado automaticamente

Verifique os logs do serviço init-connector:
```bash
docker logs init-connector
```

Se necessário, execute manualmente:
```bash
curl -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  -d @connectors/connector.json
```

Ou recrie o serviço:
```bash
docker compose up -d init-connector
```

### Ver logs do conector

```bash
docker logs connect
docker logs init-connector
```

### Reiniciar serviços

```bash
docker compose restart connect
docker compose restart init-connector
```

### Limpar tudo e começar do zero

```bash
docker compose down -v
docker compose up -d
```

## 📊 Evidências de Execução

O script de validação (`05_validacao.py`) gera um relatório completo mostrando:
- ✅ Total de registros no source
- ✅ Total de registros no destination
- ✅ Total de arquivos no MinIO
- ✅ Comparação de sincronização entre source e destination

## 🔗 Portas Utilizadas

- **2181**: Zookeeper
- **9092**: Kafka (interno)
- **9094**: Kafka (externo)
- **8081**: Schema Registry
- **8083**: Kafka Connect
- **8080**: Kafka UI
- **5434**: Postgres Source (mapeado externamente, interno 5432)
- **5433**: Postgres Destination
- **9000**: MinIO API
- **9001**: MinIO Console

## 📝 Notas

- O conector Debezium é criado automaticamente pelo serviço `init-connector` ao subir o docker-compose
- O serviço `init-connector` aguarda o Kafka Connect estar saudável antes de criar o conector
- Os consumers devem estar rodando para replicar dados nos destinos
- O tópico Kafka é criado automaticamente pelo Debezium
- Todos os eventos CDC (INSERT, UPDATE, DELETE) são capturados e replicados
- A porta do Postgres Source foi alterada para 5434 para evitar conflito com PostgreSQL local

## 🎯 Checklist de Entrega

- ✅ `docker-compose.yml` com todos os serviços
- ✅ Tópicos no Kafka configurados
- ✅ Consumidores/Produtores configurados
- ✅ Scripts de carga inicial
- ✅ Scripts de mutações (INSERT/UPDATE/DELETE)
- ✅ Instruções passo a passo
- ✅ Consultas de validação nos destinos
- ✅ Estrutura de diretórios organizada
