# Pipeline CDC Fim a Fim

Este projeto implementa um pipeline completo de **Change Data Capture (CDC)** para replicação de dados em tempo real, utilizando **mudanças lógicas do banco de dados** como fonte primária de dados. O pipeline demonstra a captura de mudanças (INSERT, UPDATE, DELETE) através da replicação lógica do PostgreSQL e sua distribuição para múltiplos destinos.

## 🎯 Conceito Principal

**A fonte de dados são as mudanças lógicas capturadas diretamente do WAL (Write-Ahead Log) do PostgreSQL**, através da replicação lógica (`wal_level=logical`). O Debezium conecta-se ao PostgreSQL via slot de replicação lógica, capturando cada mudança (INSERT, UPDATE, DELETE) em tempo real sem necessidade de modificar a aplicação fonte ou usar polling.

## 📚 Informações do Projeto

**Instituição**: Universidade de Fortaleza (UNIFOR)  
**Disciplina**: Arquitetura de Microserviços  
**Curso**: MBA Engenharia de Dados

### 👥 Integrantes

- **Rafael Lima Tavares** - Matrícula: [ADICIONAR MATRÍCULA]
- **Dante Dantes** - Matrícula: [ADICIONAR MATRÍCULA]

## 🎯 O que foi Desenvolvido

Este trabalho implementa um pipeline CDC completo e reprodutível que demonstra:

1. **Captura de Mudanças Lógicas em Tempo Real**
   - **Fonte de dados: Mudanças lógicas do banco** via replicação lógica (WAL)
   - Configuração do PostgreSQL com `wal_level=logical` para habilitar replicação lógica
   - Uso do Debezium conectado via slot de replicação lógica para capturar eventos de INSERT, UPDATE e DELETE
   - Captura em tempo real sem polling ou modificações na aplicação fonte
   - Integração com Kafka e Schema Registry usando Avro

2. **Distribuição para Múltiplos Destinos**
   - **PostgreSQL Sink**: Replicação síncrona usando JDBC Sink Connector
   - **MinIO (S3)**: Armazenamento em formato Parquet para análise de dados
   - Suporte para adicionar mais destinos (DuckDB, Elasticsearch, etc.)

3. **Automação e Reprodutibilidade**
   - Docker Compose para orquestração de todos os serviços
   - Scripts automatizados para setup, carga inicial e validação
   - Documentação completa com passo a passo

4. **Validação e Testes**
   - Scripts de teste para todas as operações (INSERT/UPDATE/DELETE)
   - Validação automática da replicação nos destinos
   - Verificação de integridade dos dados

### 🔧 Tecnologias Utilizadas

- **Apache Kafka**: Broker de mensagens para streaming de dados
- **Schema Registry**: Gerenciamento de schemas Avro
- **Debezium**: Conector source para CDC do PostgreSQL
- **Kafka Connect**: Framework para integração de sistemas
- **PostgreSQL**: Banco de dados relacional (fonte e destino)
- **MinIO**: Armazenamento S3-compatible
- **Docker & Docker Compose**: Containerização e orquestração
- **Python**: Scripts de carga e testes
- **Avro**: Serialização de dados com schema

## 📋 Arquitetura

```
┌─────────────────────┐
│  PostgreSQL Fonte   │ (com replicação lógica)
│   (source_db)       │
└──────────┬──────────┘
           │
           │ WAL (Write-Ahead Log)
           │
           ▼
┌─────────────────────┐
│   Debezium Source   │ (captura mudanças)
│     Connector       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Kafka + Schema    │ (tópicos Avro)
│     Registry        │
└──────────┬──────────┘
           │
           ├─────────────────┬─────────────────┐
           ▼                 ▼                 ▼
    ┌──────────┐      ┌──────────┐      ┌──────────┐
    │PostgreSQL│      │  MinIO   │      │  DuckDB   │
    │  Sink    │      │  (S3)    │      │ (opcional)│
    │(sink_db) │      │ Parquet  │      │           │
    └──────────┘      └──────────┘      └──────────┘
```

## 🛠️ Componentes

- **Kafka**: Broker de mensagens
- **Schema Registry**: Gerenciamento de schemas Avro
- **Debezium**: Conector source para captura de mudanças do PostgreSQL
- **Kafka Connect**: Framework para conectar sistemas externos
- **PostgreSQL Fonte**: Banco de dados com replicação lógica (WAL)
- **PostgreSQL Sink**: Banco de dados destino
- **MinIO**: Armazenamento S3-compatible para arquivos Parquet
- **DuckDB**: Banco de dados analítico local (opcional)

## 📁 Estrutura do Projeto

```
trabalho/
├── docker-compose.yml          # Orquestração de todos os serviços
├── connectors/                 # Configurações dos conectores
│   ├── debezium-source.json    # Conector Debezium (source)
│   ├── jdbc-sink-postgres.json # Conector JDBC Sink (PostgreSQL)
│   └── s3-sink-minio.json      # Conector S3 Sink (MinIO)
├── scripts/                    # Scripts de execução
│   ├── setup.sh                # Configuração inicial
│   ├── initial_load.py         # Carga inicial de dados
│   ├── mutations.py            # Testes de INSERT/UPDATE/DELETE
│   └── validate.sh             # Validação dos dados nos destinos
├── docs/                       # Documentação adicional (opcional)
├── requirements.txt            # Dependências Python
└── README.md                   # Este arquivo
```

## 🚀 Como Executar

### Pré-requisitos

- **Docker** e **Docker Compose** instalados
- **Python 3.8+** com `pip`
- **Git** (para clonar o repositório)

### Passo 1: Instalar Dependências Python

```bash
cd trabalho
pip install -r requirements.txt
```

### Passo 2: Subir os Serviços

```bash
docker-compose up -d
```

Este comando irá iniciar:
- Zookeeper
- Kafka
- Schema Registry
- PostgreSQL Fonte (porta 5433)
- PostgreSQL Sink (porta 5434)
- MinIO (portas 9000 e 9001)
- Kafka Connect (porta 8083)

**⏱️ Aguarde aproximadamente 60-90 segundos** para todos os serviços estarem prontos.

### Passo 3: Configurar o Pipeline

Execute o script de setup que irá:
- Criar a tabela `products` no PostgreSQL fonte
- Configurar o bucket no MinIO
- Registrar os conectores (Debezium, JDBC Sink, S3 Sink)

```bash
bash scripts/setup.sh
```

**Importante**: O script aguarda automaticamente os serviços estarem prontos antes de continuar.

### Passo 4: Carga Inicial

Insere dados iniciais na tabela `products` do banco fonte:

```bash
python scripts/initial_load.py
```

Este script insere 5 produtos iniciais que serão capturados pelo Debezium e replicados para os destinos.

### Passo 5: Testar Mutações (INSERT/UPDATE/DELETE)

Execute o script que testa todas as operações:

```bash
python scripts/mutations.py
```

Este script executa:
1. **INSERT**: Inserção de um novo produto
2. **UPDATE**: Atualização de preço e estoque
3. **DELETE**: Remoção de um produto
4. **MÚLTIPLAS ATUALIZAÇÕES**: Várias atualizações sequenciais

### Passo 6: Validar os Dados

Verifique se os dados foram replicados corretamente nos destinos:

```bash
bash scripts/validate.sh
```

Este script mostra:
- Total de produtos no PostgreSQL Sink
- Lista de produtos replicados
- Comparação entre fonte e sink
- Arquivos no MinIO (S3)
- Status dos conectores
- Informações sobre os tópicos Kafka

## 🔍 Verificações Manuais

### Verificar Dados no PostgreSQL Sink

```bash
docker exec -it postgres-sink psql -U postgres -d sink_db -c "SELECT * FROM products ORDER BY id;"
```

### Verificar Tópicos Kafka

```bash
docker exec kafka kafka-topics --list --bootstrap-server kafka:29092
```

### Verificar Mensagens no Tópico

```bash
docker exec kafka kafka-console-consumer \
  --bootstrap-server kafka:29092 \
  --topic cdc-source-server.public.products \
  --from-beginning \
  --max-messages 5
```

### Verificar Arquivos no MinIO

Acesse o console do MinIO em: http://localhost:9001
- Usuário: `minioadmin`
- Senha: `minioadmin`

Ou via CLI:

```bash
docker exec minio mc ls local/cdc-data --recursive
```

### Verificar Status dos Conectores

```bash
# Listar todos os conectores
curl http://localhost:8083/connectors

# Status de um conector específico
curl http://localhost:8083/connectors/debezium-postgres-source/status | python3 -m json.tool
```

## 📊 Interfaces Web

- **Kafka UI**: http://localhost:8080 (se configurado)
- **MinIO Console**: http://localhost:9001
  - Usuário: `minioadmin`
  - Senha: `minioadmin`
- **Schema Registry**: http://localhost:8082

## 🐛 Troubleshooting

### Problema: Conectores não iniciam

**Solução**: Verifique os logs do Kafka Connect:

```bash
docker logs kafka-connect
```

### Problema: Debezium não captura mudanças

**Verificações**:
1. Confirme que o PostgreSQL fonte tem `wal_level=logical`:
   ```bash
   docker exec postgres-source psql -U postgres -d source_db -c "SHOW wal_level;"
   ```

2. Verifique se o slot de replicação foi criado:
   ```bash
   docker exec postgres-source psql -U postgres -d source_db -c "SELECT * FROM pg_replication_slots;"
   ```

3. Verifique os logs do Debezium:
   ```bash
   docker logs kafka-connect | grep debezium
   ```

### Problema: Dados não aparecem no Sink

**Verificações**:
1. Confirme que o conector JDBC Sink está RUNNING:
   ```bash
   curl http://localhost:8083/connectors/jdbc-sink-postgres/status
   ```

2. Verifique se há erros no conector:
   ```bash
   docker logs kafka-connect | grep -i error
   ```

3. Confirme que o tópico tem mensagens:
   ```bash
   docker exec kafka kafka-console-consumer \
     --bootstrap-server kafka:29092 \
     --topic cdc-source-server.public.products \
     --from-beginning \
     --max-messages 1
   ```

### Problema: Arquivos não aparecem no MinIO

**Causa**: O S3 Sink Connector só escreve arquivos quando:
- O `flush.size` é atingido (10 mensagens por padrão neste projeto)
- O `rotate.interval.ms` é atingido (30 segundos por padrão neste projeto)

**Solução**: 
1. Aguarde alguns segundos após executar mutações
2. Execute mais mutações para atingir o `flush.size`
3. Verifique os logs do S3 connector:
   ```bash
   docker logs kafka-connect | grep s3-sink
   ```

**Nota**: O S3 connector está configurado com credenciais fixas para MinIO (`minioadmin/minioadmin`). Se você alterar as credenciais do MinIO, atualize também o arquivo `connectors/s3-sink-minio.json`.

### Problema: Erro de conexão com MinIO

**Solução**: Verifique se o MinIO está rodando:

```bash
docker ps | grep minio
```

Se não estiver, reinicie:

```bash
docker-compose restart minio
```

## 🧹 Limpeza

Para parar e remover todos os containers e volumes:

```bash
docker-compose down -v
```

**⚠️ Atenção**: Isso apagará todos os dados!

Para apenas parar os serviços (mantendo dados):

```bash
docker-compose stop
```

## 📝 Evidências de Execução

### Consultas de Validação

#### PostgreSQL Sink - Contar produtos
```sql
SELECT COUNT(*) FROM products;
```

#### PostgreSQL Sink - Listar todos os produtos
```sql
SELECT id, name, price, stock, category, updated_at 
FROM products 
ORDER BY id;
```

#### PostgreSQL Sink - Verificar última atualização
```sql
SELECT MAX(updated_at) as ultima_atualizacao FROM products;
```

#### Comparar Fonte vs Sink
```bash
# Fonte
docker exec postgres-source psql -U postgres -d source_db -c "SELECT COUNT(*) FROM products;"

# Sink
docker exec postgres-sink psql -U postgres -d sink_db -c "SELECT COUNT(*) FROM products;"
```

### Verificar Schemas no Schema Registry

```bash
curl http://localhost:8082/subjects | python3 -m json.tool
```

## 🎯 Checklist de Entrega

- [x] `docker-compose.yml` com todos os serviços
- [x] Conectores configurados (Debezium source + 2+ sinks)
- [x] Scripts de carga inicial e mutações
- [x] Scripts de validação
- [x] README com instruções passo a passo
- [x] Demonstração de INSERT/UPDATE/DELETE
- [x] Evidências de replicação para ≥ 2 destinos

## 📚 Referências

- [Debezium Documentation](https://debezium.io/documentation/)
- [Kafka Connect Documentation](https://kafka.apache.org/documentation/#connect)
- [Confluent S3 Sink Connector](https://docs.confluent.io/kafka-connect-s3-sink/current/overview.html)
- [PostgreSQL Logical Replication](https://www.postgresql.org/docs/current/logical-replication.html)

## 📝 Conclusão

Este trabalho demonstra a implementação prática de um pipeline CDC completo, desde a captura de mudanças no banco de dados fonte até a distribuição para múltiplos destinos, utilizando tecnologias modernas de streaming de dados e integração.

### ✅ Objetivos Alcançados

- ✅ Pipeline CDC reprodutível com Docker Compose
- ✅ Captura de INSERT, UPDATE e DELETE em tempo real
- ✅ Replicação para pelo menos 2 destinos (PostgreSQL e MinIO)
- ✅ Uso de Schema Registry com Avro
- ✅ Scripts automatizados de setup, carga e validação
- ✅ Documentação completa e passo a passo

### 📊 Evidências de Execução

O pipeline foi testado e validado com sucesso, demonstrando:
- Captura de mudanças via Debezium
- Replicação síncrona para PostgreSQL Sink
- Armazenamento em formato Parquet no MinIO
- Integridade dos dados entre fonte e destinos

---

## 👥 Autores

**Rafael Lima Tavares** - Matrícula: [ADICIONAR MATRÍCULA]  
**Dante Dantes** - Matrícula: [ADICIONAR MATRÍCULA]

**Instituição**: Universidade de Fortaleza (UNIFOR)  
**Disciplina**: Arquitetura de Microserviços  
**Curso**: MBA Engenharia de Dados

---

**Última atualização**: Dezembro 2024

