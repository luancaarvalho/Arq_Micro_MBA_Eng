<h1 align="center">CDC Pipeline — Kafka + Debezium + PostgreSQL + MinIO</h1>

<p align="center">
  <strong>Pipeline end-to-end</strong> de captura de mudanças (CDC) usando <strong>Debezium</strong> + <strong>Kafka</strong>, 
  replicando dados de um PostgreSQL fonte para <strong>PostgreSQL Sink</strong> e <strong>MinIO</strong>.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Kafka-7.4.x-orange?style=flat-square" alt="Kafka 7.4.x" />
  <img src="https://img.shields.io/badge/Debezium-2.3-blue?style=flat-square" alt="Debezium 2.3" />
  <img src="https://img.shields.io/badge/PostgreSQL-15-336791?style=flat-square" alt="PostgreSQL 15" />
  <img src="https://img.shields.io/badge/MinIO-latest-green?style=flat-square" alt="MinIO latest" />
  <img src="https://img.shields.io/badge/Docker%20Compose-2.x-lightgrey?style=flat-square" alt="Docker Compose 2.x" />
  <img src="https://img.shields.io/badge/Python-3.10+-3776ab?style=flat-square" alt="Python 3.10+" />
</p>

<hr>

## Objetivo

Atender ao trabalho de **Pipeline CDC fim a fim**, construindo um fluxo reprodutível de replicação de dados:

```
Postgres fonte (replicação lógica)
    → Debezium
    → Kafka (+ Schema Registry)
    → 2 destinos:
        ├─ PostgreSQL Sink (JDBC Sink Connector)
        └─ MinIO (consumidor Python)
```

<hr>

## O que este projeto entrega

<table>
  <tr>
    <th>Componente</th>
    <th>Descrição</th>
  </tr>
  <tr>
    <td><strong>Captura CDC</strong></td>
    <td>INSERT/UPDATE/DELETE na tabela <code>products</code></td>
  </tr>
  <tr>
    <td><strong>Debezium Source</strong></td>
    <td>Lê WAL e publica no tópico <code>cdc-source-server.public.products</code></td>
  </tr>
  <tr>
    <td><strong>JDBC Sink</strong></td>
    <td>Replica dados para <code>postgres-sink</code> em modo upsert</td>
  </tr>
  <tr>
    <td><strong>MinIO Storage</strong></td>
    <td>Armazena eventos em <code>cdc-data/messages/AAAA/MM/DD/*.json</code></td>
  </tr>
  <tr>
    <td><strong>Scripts Python</strong></td>
    <td>Setup, carga inicial, mutações, validação e consumidor CDC</td>
  </tr>
</table>

<hr>

## Arquitetura

```
┌─────────────────┐         ┌──────────────────────┐
│  postgres-src   │────────▶│  Debezium Source     │
│   (WAL/CDC)     │         │   (Postgres)         │
└─────────────────┘         └──────────┬───────────┘
                                       │
                            ┌──────────▼───────────┐
                            │  Kafka + Schema Reg  │
                            └──────────┬───────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
            ┌──────────────────┐  ┌─────────────┐  ┌─────────────┐
            │ JDBC Sink        │  │  Consumer   │  │  Validação  │
            │ postgres-sink    │  │  Python     │  │  & Monit.   │
            │ (upsert)         │  │  → MinIO    │  │             │
            └──────────────────┘  └─────────────┘  └─────────────┘
```

### Estrutura do Projeto

```
trabalho/
├── docker-compose.yml          # Orquestração dos serviços
├── requirements.txt            # Dependências Python
├── connectors/
│   ├── debezium-source.json       # Config Debezium Postgres Source
│   └── jdbc-sink-postgres.json    # Config JDBC Sink
└── scripts/
    ├── setup.py                   # Setup inicial e registro de conectores
    ├── initial_load.py            # Carga inicial de dados
    ├── mutations.py               # INSERT/UPDATE/DELETE para testes
    ├── validate.py                # Validação de replicação
    └── kafka_to_minio.py          # Consumidor Kafka → MinIO
```

<hr>

## Pré-requisitos

<ul>
  <li><strong>Docker Desktop / Docker Engine</strong> com Docker Compose v2+</li>
  <li><strong>Python 3.10+</strong> instalado localmente</li>
  <li><strong>Portas livres:</strong>
    <ul>
      <li><code>5433</code> – PostgreSQL Source</li>
      <li><code>5434</code> – PostgreSQL Sink</li>
      <li><code>9092</code> – Kafka (PLAINTEXT_HOST)</li>
      <li><code>8083</code> – Kafka Connect</li>
      <li><code>8082</code> – Schema Registry</li>
      <li><code>9000 / 9001</code> – MinIO (API e Console)</li>
    </ul>
  </li>
</ul>

<hr>

## Serviços do docker-compose.yml

| Serviço             | Função                | Porta      |
| ------------------- | --------------------- | ---------- |
| **zookeeper**       | Coordenação Kafka     | -          |
| **kafka**           | Broker Kafka          | 9092       |
| **schema-registry** | Schemas Avro/JSON     | 8082       |
| **postgres-source** | BD fonte (source_db)  | 5433       |
| **postgres-sink**   | BD destino (sink_db)  | 5434       |
| **minio**           | Storage S3-compatível | 9000, 9001 |
| **kafka-connect**   | Debezium + JDBC       | 8083       |

<hr>

## Dependências Python

```bash
pip install -r requirements.txt
```

**Principais libs:**

- `psycopg2-binary` – Conexão PostgreSQL
- `minio` – Cliente MinIO/S3
- `confluent-kafka` – Consumer Kafka

<hr>

## Guia de Execução (Passo a Passo)

### 1 Subir os Containers

```bash
cd trabalho/
docker compose up -d
```

### 2 Setup do Pipeline

```bash
python scripts/setup.py
```

**Este script:**

- Aguarda Postgres e Kafka Connect ficarem prontos
- Cria tabela `products` no `source_db`
- Configura MinIO e bucket `cdc-data`
- Registra conectores (Debezium + JDBC Sink)
- Mostra status dos conectores

### 3 Carga Inicial de Dados

```bash
python scripts/initial_load.py
```

**Popula:** 5 produtos iniciais na tabela `products` do `postgres-source`

> **Nota:** Ao rodar novamente, adiciona mais produtos (sem truncate automático)

### 4 Executar Mutações (INSERT/UPDATE/DELETE)

```bash
python scripts/mutations.py
```

**O script executa:**

- INSERT de novo produto
- UPDATE de preço/estoque
- DELETE de produto
- Múltiplos UPDATEs em sequência

**Resultado:** Todos os eventos CDC são capturados pelo Debezium

### 5 Consumidor Kafka → MinIO (Opcional)

```bash
python scripts/kafka_to_minio.py
```

**Consome eventos e armazena em MinIO** (modo background)

### 6 Validar o Pipeline

```bash
python scripts/validate.py
```

**Valida:**

- Replicação em postgres-source e postgres-sink
- Arquivos JSON em MinIO
- Status dos conectores Kafka Connect

<hr>

## Fluxo Completo Recomendado

```bash
# Terminal 1: Containers
docker compose up -d

# Terminal 2: Setup
python scripts/setup.py

# Terminal 3: Testes
python scripts/initial_load.py
python scripts/mutations.py
python scripts/validate.py
```

<hr>

<h2>Licença</h2>
<p>Projeto acadêmico — uso educacional.</p>

<p>Desenvolvido por:<br/>
<a href="https://www.linkedin.com/in/rafaeld3v/" target="_blank">Rafael Tavares (LinkedIn)</a> - 2517595<br/>
<a href="https://www.linkedin.com/in/dantedod/" target="_blank">Dante Dantas (LinkedIn)</a> - 2518583</p>
