# Arquitetura de Microserviços - MBA Engenharia de Dados

Repositório da disciplina de Arquitetura de Microserviços do MBA em Engenharia de Dados.

## 📚 Estrutura do Repositório

Este repositório contém as aulas práticas e o trabalho final da disciplina:

```
Arq_Micro_MBA_Eng/
├── aula_01/          # Introdução ao Kafka
├── aula_02/          # Schemas e Serialização
├── aula_03/          # Tópicos, Partições, Replicação e Connect
├── aula_04/          # Domain-Driven Design
├── aula_05/          # CQRS e Transações
└── trabalho/         # Trabalho Final: Pipeline CDC Fim a Fim
```

## 🎯 Trabalho Final: Pipeline CDC Fim a Fim

### Descrição

O trabalho final implementa um **pipeline completo de Change Data Capture (CDC)** que utiliza **mudanças lógicas do banco de dados** como fonte de dados. O objetivo é demonstrar a captura em tempo real de eventos de INSERT, UPDATE e DELETE através da replicação lógica do PostgreSQL e sua distribuição para múltiplos destinos.

### Conceito Principal

O pipeline utiliza a **replicação lógica do PostgreSQL** (WAL - Write-Ahead Log) como fonte primária de dados. As mudanças lógicas capturadas do banco de dados são transformadas em eventos que fluem através do Kafka até os destinos finais.

### Arquitetura Implementada

```
┌─────────────────────────────────┐
│  PostgreSQL Fonte              │
│  (Replicação Lógica - WAL)     │ ← FONTE: Mudanças Lógicas do Banco
│  wal_level=logical             │
└──────────────┬──────────────────┘
               │
               │ Mudanças Lógicas (INSERT/UPDATE/DELETE)
               │
               ▼
┌─────────────────────────────────┐
│   Debezium Source Connector    │ ← Captura mudanças via WAL
│   (Logical Replication Slot)    │
└──────────────┬──────────────────┘
               │
               │ Eventos CDC (Avro)
               │
               ▼
┌─────────────────────────────────┐
│   Kafka + Schema Registry       │ ← Streaming de Eventos
│   (Tópicos Avro)                │
└──────────────┬──────────────────┘
               │
               ├──────────────────┬──────────────────┐
               ▼                  ▼                  ▼
    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
    │ PostgreSQL   │    │    MinIO      │    │   (Futuro)   │
    │    Sink      │    │   (S3/Parquet)│    │   DuckDB     │
    │  (JDBC Sink) │    │  (S3 Sink)    │    │              │
    └──────────────┘    └──────────────┘    └──────────────┘
```

### Características Principais

1. **Fonte de Dados: Mudanças Lógicas do Banco**
   - Utiliza a replicação lógica do PostgreSQL (`wal_level=logical`)
   - Captura mudanças através do WAL (Write-Ahead Log)
   - Não requer modificações na aplicação fonte
   - Captura eventos de INSERT, UPDATE e DELETE automaticamente

2. **Captura de Mudanças (CDC)**
   - Debezium conecta-se ao PostgreSQL via slot de replicação lógica
   - Cada mudança no banco gera um evento no Kafka
   - Schemas Avro garantem compatibilidade e evolução

3. **Distribuição para Múltiplos Destinos**
   - **PostgreSQL Sink**: Replicação síncrona via JDBC Sink Connector
   - **MinIO (S3)**: Armazenamento em formato Parquet para análise
   - Arquitetura extensível para adicionar mais destinos

### Tecnologias Utilizadas

- **PostgreSQL**: Banco de dados com replicação lógica habilitada
- **Debezium**: Conector source para CDC via replicação lógica
- **Apache Kafka**: Broker de mensagens para streaming
- **Schema Registry**: Gerenciamento de schemas Avro
- **Kafka Connect**: Framework para integração de sistemas
- **MinIO**: Armazenamento S3-compatible
- **Docker & Docker Compose**: Containerização e orquestração

### Estrutura do Trabalho

O trabalho está localizado na pasta `trabalho/` e contém:

```
trabalho/
├── docker-compose.yml          # Orquestração de todos os serviços
├── connectors/                 # Configurações dos conectores
│   ├── debezium-source.json    # Conector Debezium (captura mudanças lógicas)
│   ├── jdbc-sink-postgres.json # Conector JDBC Sink (PostgreSQL)
│   └── s3-sink-minio.json      # Conector S3 Sink (MinIO/Parquet)
├── scripts/                    # Scripts de execução
│   ├── setup.sh                # Configuração inicial do pipeline
│   ├── initial_load.py         # Carga inicial de dados
│   ├── mutations.py            # Testes de INSERT/UPDATE/DELETE
│   ├── validate.sh             # Validação dos dados nos destinos
│   └── reset.sh                # Reset do ambiente
├── requirements.txt            # Dependências Python
└── README.md                   # Documentação completa do trabalho
```

### Como Executar

Para executar o trabalho, siga as instruções detalhadas no README do trabalho:

```bash
cd trabalho
# Siga as instruções em trabalho/README.md
```

**Passos rápidos:**
1. `docker-compose up -d` - Subir todos os serviços
2. `bash scripts/setup.sh` - Configurar o pipeline
3. `python scripts/initial_load.py` - Carga inicial
4. `python scripts/mutations.py` - Testar mutações
5. `bash scripts/validate.sh` - Validar resultados

### Diferenciais da Implementação

1. **Uso de Replicação Lógica**: A fonte de dados são as mudanças lógicas capturadas diretamente do WAL do PostgreSQL, não polling ou triggers
2. **Zero Impacto na Aplicação**: Não requer modificações no código da aplicação fonte
3. **Tempo Real**: Captura de mudanças em tempo real através do slot de replicação
4. **Múltiplos Destinos**: Demonstração de distribuição para pelo menos 2 destinos diferentes
5. **Reprodutibilidade**: Pipeline completamente containerizado e automatizado

### Requisitos Atendidos

✅ Pipeline CDC reprodutível (Docker Compose)  
✅ Fonte de dados: Mudanças lógicas do banco (WAL)  
✅ Captura de INSERT, UPDATE e DELETE  
✅ Distribuição para ≥ 2 destinos (PostgreSQL e MinIO)  
✅ Uso de Schema Registry com Avro  
✅ Scripts automatizados de setup e validação  
✅ Documentação completa

### Integrantes

- **Rafael Lima Tavares** - Matrícula: [ADICIONAR MATRÍCULA]
- **Dante Dantes** - Matrícula: [ADICIONAR MATRÍCULA]

**Instituição**: Universidade de Fortaleza (UNIFOR)  
**Disciplina**: Arquitetura de Microserviços  
**Curso**: MBA Engenharia de Dados

---

## 📖 Aulas Práticas

### Aula 01: Introdução ao Kafka
Demonstrações básicas de produtores e consumidores Kafka.

### Aula 02: Schemas e Serialização
Uso de Avro e Schema Registry para garantir contratos de dados.

### Aula 03: Tópicos, Partições, Replicação e Connect
- Partições e offsets
- Replicação e tolerância a falhas
- Kafka Connect e conectores
- Consumer groups e lag

### Aula 04: Domain-Driven Design
Aplicação de conceitos de DDD em sistemas distribuídos.

### Aula 05: CQRS e Transações
- Command Query Responsibility Segregation
- Transações distribuídas no Kafka
- Read models e projections

---

## 🛠️ Pré-requisitos

- Docker e Docker Compose
- Python 3.8+
- Git

## 📝 Licença

Este repositório contém material didático da disciplina de Arquitetura de Microserviços.

---

**Última atualização**: Dezembro 2024
