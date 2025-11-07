# Aula 02 — Demonstrações Kafka

Esta pasta contém scripts e demos práticos para entender conceitos fundamentais do Kafka.

## Estrutura

```
aula_02/
└── DEMO_1/              # Demonstrações de Kafka
    ├── generate_1m_events.py    # Comparação JSON vs Avro
    ├── consumer_group_demo.py  # Consumer Groups e Rebalancing
    ├── offset_demo.py          # Offsets e Seek
    ├── schema.avsc             # Schema Avro
    ├── environment.yml         # Ambiente conda
    └── README.md               # Documentação detalhada
```

## Pré-requisitos

Antes de executar os scripts, certifique-se de que:

1. **Kafka está rodando** (via `aula_01`):
   ```bash
   cd ../aula_01
   docker compose up -d
   ```

2. **Ambiente conda está criado**:
   ```bash
   cd DEMO_1
   conda env create -f environment.yml
   conda activate demo1-kafka
   ```

## Demos Disponíveis

### 1. Comparação JSON vs Avro
**Arquivo**: `DEMO_1/generate_1m_events.py`

Gera 1 milhão de eventos e compara o tamanho de armazenamento entre JSON e Avro.

### 2. Consumer Groups
**Arquivo**: `DEMO_1/consumer_group_demo.py`

Demonstra como múltiplos consumers dividem o trabalho e como funciona o rebalancing.

### 3. Offsets
**Arquivo**: `DEMO_1/offset_demo.py`

Demonstra como funcionam offsets e como controlar de onde começar a ler mensagens.

## Documentação Detalhada

Para instruções completas de cada demo, consulte:
- [`DEMO_1/README.md`](DEMO_1/README.md)

