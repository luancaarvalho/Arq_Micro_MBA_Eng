# DEMO_1 — Kafka: JSON vs Avro + Offsets e Consumer Groups

Esta demonstração tem dois objetivos principais:

1. **Comparar armazenamento JSON vs Avro**: Gerar 1 milhão de eventos e comparar o tamanho em disco entre os dois formatos
2. **Demonstrar Offsets e Consumer Groups**: Scripts simples para entender como funcionam esses conceitos fundamentais do Kafka

## Estrutura

```
DEMO_1/
├── environment.yml          # Ambiente conda reprodutível
├── schema.avsc             # Schema Avro para eventos Order
├── generate_1m_events.py    # Gera eventos JSON e Avro (1 milhão)
├── consumer_group_demo.py   # Demonstra consumer groups
├── offset_demo.py           # Demonstra offsets
└── README.md                # Este arquivo
```

## Pré-requisitos

- Docker e Docker Compose rodando (Kafka, Schema Registry)
- Conda instalado
- Os serviços devem estar acessíveis em:
  - Kafka: `localhost:9092`
  - Schema Registry: `http://localhost:8082`

## Setup do Ambiente

### 1. Criar e ativar o ambiente conda

```bash
cd DEMO_1
conda env create -f environment.yml
conda activate demo1-kafka
```

### 2. Verificar se os serviços Kafka estão rodando

```bash
# Na pasta aula_01 (irmã desta)
cd ../aula_01
docker compose ps
```

Você deve ver:
- `zookeeper` (porta 2181)
- `kafka` (porta 9092)
- `schema-registry` (porta 8082)
- `kafka-ui` (porta 8080)
- `akhq` (porta 8081)

## Parte 1: Comparação JSON vs Avro

### Objetivo

Gerar o mesmo evento (Order) em dois tópicos diferentes:
- `orders-json`: Mensagens em formato JSON
- `orders-avro`: Mensagens em formato Avro (com Schema Registry)

Depois, comparar o tamanho em disco ocupado por cada tópico.

### Executar

```bash
python generate_1m_events.py
```

Por padrão, o script gera **1 milhão de eventos** (500k JSON + 500k Avro). Você pode alterar o número de eventos com:

```bash
python generate_1m_events.py --target-events 2000000  # 2 milhões
```

### O que acontece

1. O script cria os tópicos `orders-json` e `orders-avro` automaticamente
2. Registra o schema Avro no Schema Registry
3. Gera eventos usando Faker (dados realistas de pedidos)
4. Publica o **mesmo evento** em ambos os tópicos simultaneamente
5. Monitora o progresso e mostra estatísticas

### Medir tamanho em disco

Após a geração terminar, execute:

```bash
docker exec kafka bash -c 'du -sh /var/lib/kafka/data/orders-json-* /var/lib/kafka/data/orders-avro-*'
```

**Resultado esperado**: O tópico Avro deve ocupar significativamente menos espaço que o JSON (tipicamente 30-50% menos).

### Por que a diferença?

- **JSON**: Texto legível, repetição de chaves em cada mensagem, sem compressão de schema
- **Avro**: Binário compacto, schema compartilhado (não repetido), tipos otimizados

### Visualizar nas UIs

- **Kafka UI**: http://localhost:8080
  - Navegue até os tópicos `orders-json` e `orders-avro`
  - Veja as mensagens e compare o tamanho
- **AKHQ**: http://localhost:8081
  - Veja os schemas registrados no Schema Registry
  - Compare o tamanho das mensagens

## Parte 2: Consumer Groups

### Objetivo

Demonstrar como múltiplos consumers em um mesmo consumer group dividem o trabalho de ler mensagens de um tópico com múltiplas partitions.

### Executar

#### Passo 1: Produzir mensagens

Em um terminal:

```bash
python consumer_group_demo.py --produce
```

Isso cria o tópico `cg-demo` com 3 partitions e envia 30 mensagens.

#### Passo 2: Consumir com 1 consumer

Em outro terminal:

```bash
python consumer_group_demo.py --consumer-id consumer-1
```

Você verá que este consumer recebe mensagens de **todas as 3 partitions**.

#### Passo 3: Adicionar um segundo consumer

Em um terceiro terminal:

```bash
python consumer_group_demo.py --consumer-id consumer-2
```

**O que acontece**: O Kafka faz **rebalancing** e redistribui as partitions entre os dois consumers. Agora cada consumer lê de aproximadamente 1-2 partitions.

### Conceitos demonstrados

- **Consumer Group**: Múltiplos consumers trabalhando juntos
- **Partition Assignment**: Cada partition é atribuída a apenas um consumer do grupo
- **Rebalancing**: Quando consumers entram/saem, o Kafka redistribui as partitions
- **Offset Tracking**: Cada consumer group mantém seus próprios offsets

## Parte 3: Offsets

### Objetivo

Demonstrar como funcionam offsets e como controlar de onde começar a ler mensagens.

### Executar

#### Passo 1: Produzir mensagens

```bash
python offset_demo.py --produce
```

Isso cria o tópico `offset-demo` e envia 10 mensagens.

#### Passo 2: Consumir normalmente

```bash
python offset_demo.py
```

O consumer lê todas as mensagens e salva o offset no consumer group `offset-demo-default`.

#### Passo 3: Consumir novamente (mesmo group)

```bash
python offset_demo.py
```

**O que acontece**: Não há mensagens novas, então nada é lido. O offset foi salvo e o consumer continua de onde parou.

#### Passo 4: Criar um novo consumer group

```bash
python offset_demo.py --new-group
```

**O que acontece**: Um novo consumer group é criado (com nome único) e lê **todas as mensagens do início**, pois não tem offsets salvos.

#### Passo 5: Fazer seek para o início

```bash
python offset_demo.py --seek-beginning
```

**O que acontece**: Mesmo usando o consumer group padrão (que já tem offsets salvos), o `seek` força a leitura a partir do offset 0, ignorando os offsets salvos.

### Conceitos demonstrados

- **Offset**: Posição de leitura de cada consumer group em cada partition
- **Auto Commit**: Offsets são salvos automaticamente
- **New Consumer Group**: Sempre começa do início (ou `auto.offset.reset`)
- **Seek**: Permite ignorar offsets salvos e ler de uma posição específica

## Limpeza

Para remover os tópicos criados (opcional):

```bash
# Via Kafka UI ou AKHQ, ou usando kafka CLI:
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --delete --topic orders-json
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --delete --topic orders-avro
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --delete --topic cg-demo
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --delete --topic offset-demo
```

Para remover o ambiente conda:

```bash
conda deactivate
conda env remove -n demo1-kafka
```

## Troubleshooting

### Erro: "Connection refused" ao conectar no Kafka

- Verifique se os containers estão rodando: `docker compose ps`
- Verifique se a porta 9092 está acessível: `telnet localhost 9092`

### Erro: "Schema Registry not available"

- Verifique se o Schema Registry está rodando: `curl http://localhost:8082/subjects`
- Verifique os logs: `docker logs schema-registry`

### Erro ao instalar confluent-kafka no Windows

O `confluent-kafka` requer `librdkafka`. No Windows, pode ser necessário:
- Instalar via conda-forge (já configurado no `environment.yml`)
- Ou usar WSL2

### Script muito lento para gerar 1 milhão de eventos

- Isso é esperado! Gerar 1 milhão de eventos pode levar alguns minutos
- Reduza o número para testes: `python generate_1m_events.py --target-events 100000` (100k eventos)

## Notas Didáticas

### Por que dois tópicos separados?

Para comparação justa, precisamos do **mesmo evento** em ambos os formatos. Como não podemos ter duas codificações diferentes na mesma mensagem, usamos dois tópicos com a mesma semântica.

### Compression.type = none

O script usa `compression.type=none` nos producers para evidenciar a diferença entre JSON e Avro sem interferência de compressão. Em produção, você normalmente usaria compressão (snappy, gzip, lz4).

### Schema Registry

O Schema Registry permite:
- Versionamento de schemas
- Validação de compatibilidade
- Reutilização de schemas (economia de espaço)
- Evolução de schemas sem quebrar consumers antigos

