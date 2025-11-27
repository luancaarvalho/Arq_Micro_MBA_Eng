# Troubleshooting Demo 06

## Problemas Encontrados e Soluções

### Problema 1: NOT_ENOUGH_REPLICAS

**Erro:**
```
Messages are rejected since there are fewer in-sync replicas than required.
```

**Causa:**
- Tópico criado com `replication.factor=1`
- Configuração global `min.insync.replicas=2`
- Conflito: não é possível ter 2 réplicas in-sync se só existe 1 réplica total

**Solução:**
```bash
# Alterar configuração do tópico
docker exec kafka kafka-configs --alter \
    --entity-type topics \
    --entity-name demo-orders \
    --add-config min.insync.replicas=1 \
    --bootstrap-server kafka:29092
```

### Problema 2: Schema Null (PRINCIPAL)

**Erro:**
```
Sink connector requires records with a non-null Struct value and non-null Struct schema,
but found record with a HashMap value and null value schema.
```

**Causa:**
O JDBC Sink Connector da Confluent **SEMPRE** exige que as mensagens tenham um schema explícito (Avro, JSON Schema ou Protobuf). JSON puro sem schema não funciona.

**Soluções Possíveis:**

#### Opção A: Usar Avro com Schema Registry (RECOMENDADO)
Modificar o producer para usar Avro:

```python
from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import SerializationContext, MessageField

schema_str = '''
{
  "type": "record",
  "name": "Order",
  "fields": [
    {"name": "order_id", "type": "string"},
    {"name": "customer_name", "type": "string"},
    {"name": "product", "type": "string"},
    {"name": "amount", "type": "double"},
    {"name": "status", "type": "string"},
    {"name": "created_at", "type": "string"},
    {"name": "updated_at", "type": "string"}
  ]
}
'''

schema_registry_conf = {'url': 'http://localhost:8082'}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)
avro_serializer = AvroSerializer(schema_registry_client, schema_str)

producer_conf = {'bootstrap.servers': 'localhost:9092'}
producer = Producer(producer_conf)

order = {
    "order_id": "ORD-001",
    "customer_name": "João",
    "product": "Notebook",
    "amount": 3500.0,
    "status": "pending",
    "created_at": "2025-11-27T10:00:00",
    "updated_at": "2025-11-27T10:00:00"
}

producer.produce(
    topic='demo-orders',
    value=avro_serializer(order, SerializationContext('demo-orders', MessageField.VALUE))
)
producer.flush()
```

E atualizar o conector:
```json
{
    "name": "jdbc-sink-orders-demo",
    "config": {
        "connector.class": "io.confluent.connect.jdbc.JdbcSinkConnector",
        "tasks.max": "1",
        "topics": "demo-orders",
        "connection.url": "jdbc:postgresql://postgres:5432/demo_db",
        "connection.user": "postgres",
        "connection.password": "postgrespassword",
        "insert.mode": "upsert",
        "pk.mode": "record_value",
        "pk.fields": "order_id",
        "auto.create": "true",
        "auto.evolve": "true",
        "table.name.format": "orders",
        "value.converter": "io.confluent.connect.avro.AvroConverter",
        "value.converter.schema.registry.url": "http://schema-registry:8081"
    }
}
```

#### Opção B: Usar JSON Schema
Similar ao Avro, mas com JSON Schema em vez de Avro.

#### Opção C: Usar outro Sink Connector
O conector JDBC da Confluent é muito rigoroso. Alternativas:
- Debezium JDBC Sink (mais flexível)
- Conector customizado
- Script Python consumindo e inserindo manualmente

## Status Atual

- ✅ Kafka Connect rodando
- ✅ Plugin JDBC instalado
- ✅ Mensagens chegando ao tópico
- ❌ Conector falhando por falta de schema

## Próximos Passos

Para fazer funcionar completamente, escolha a Opção A (Avro) e:
1. Modifique `order_generator.py` para usar AvroSerializer
2. Atualize `connector-config.json` com os conversores Avro
3. Reregistre o conector
4. Execute o producer

Ou simplesmente use esta demo como exemplo didático do problema de schemas em Kafka Connect.


