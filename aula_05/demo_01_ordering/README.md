# Demo 01 — Garantia de ordem e transações no Kafka

Objetivo: mostrar como `enable.idempotence` + transações garantem ordem por chave e entregas atômicas. O produtor envia um conjunto finito de eventos, com opção de abortar para ver o consumidor ignorar mensagens.

## Pré-requisitos

1. Stack da `aula_01` rodando (`docker compose up -d`).
2. Ambiente Conda ativo:
   ```bash
   conda activate arq-microsservicos-mba
   ```
3. Criar o tópico:
   ```bash
   cd aula_05/demo_01_ordering
   bash setup.sh
   ```

## Produzindo eventos transacionais

```bash
python producer_transactions.py \
  --bootstrap-server localhost:9092 \
  --topic ordering.transactions \
  --transactional-id checkout-tx-1 \
  --events 5
```

Use `--abort` para abortar a transação e observar que o consumidor não verá os registros.

## Consumindo somente commits

```bash
python consumer_read_committed.py \
  --bootstrap-server localhost:9092 \
  --topic ordering.transactions \
  --group ordering-demo \
  --max-messages 5
```

Esse consumidor usa `isolation.level=read_committed`, provando que apenas commits aparecem e preservando ordenação por chave.
