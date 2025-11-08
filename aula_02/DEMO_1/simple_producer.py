#!/usr/bin/env python3
"""
Script simples para produzir mensagens no Kafka com Schema Registry
Execute: python simple_producer.py
"""

import json
import time
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka.schema_registry import SchemaRegistryClient
try:
    from confluent_kafka.avro import AvroProducer, loads
except ImportError:
    from confluent_kafka.schema_registry.avro import AvroProducer
    from confluent_kafka.schema_registry import loads

# Configurações
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
SCHEMA_REGISTRY_URL = "http://localhost:8082"
TOPIC_NAME = "user-events"

# Schema Avro
USER_EVENT_SCHEMA = """{
  "type": "record",
  "name": "UserEvent",
  "namespace": "com.example",
  "fields": [
    {"name": "user_id", "type": "int"},
    {"name": "username", "type": "string"},
    {"name": "email", "type": "string"},
    {"name": "action", "type": {"type": "enum", "name": "Action", "symbols": ["LOGIN", "LOGOUT", "PURCHASE", "VIEW"]}},
    {"name": "timestamp", "type": "long"},
    {"name": "metadata", "type": {"type": "map", "values": "string"}}
  ]
}"""


def main():
    print("=" * 60)
    print("Producer Kafka com Schema Registry")
    print("=" * 60)
    
    # 1. Criar tópico
    print("\n[1/3] Criando tópico...")
    admin_client = AdminClient({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})
    existing_topics = admin_client.list_topics(timeout=10).topics
    
    if TOPIC_NAME not in existing_topics:
        topic_list = [NewTopic(TOPIC_NAME, num_partitions=3, replication_factor=1)]
        futures = admin_client.create_topics(topic_list)
        for topic, future in futures.items():
            try:
                future.result()
                print(f"  ✓ Tópico '{topic}' criado!")
            except Exception as e:
                print(f"  ✗ Erro: {e}")
    else:
        print(f"  ✓ Tópico '{TOPIC_NAME}' já existe!")
    
    # 2. Registrar schema
    print("\n[2/3] Registrando schema no Schema Registry...")
    schema_registry_client = SchemaRegistryClient({'url': SCHEMA_REGISTRY_URL})
    
    try:
        schema_id = schema_registry_client.register_schema(
            subject_name=f"{TOPIC_NAME}-value",
            schema=USER_EVENT_SCHEMA
        )
        print(f"  ✓ Schema registrado! (ID: {schema_id})")
    except Exception as e:
        try:
            latest = schema_registry_client.get_latest_schema(f"{TOPIC_NAME}-value")
            print(f"  ✓ Schema já existe! (ID: {latest.schema_id})")
        except:
            print(f"  ⚠ Aviso: {e}")
    
    # 3. Produzir mensagens
    print("\n[3/3] Produzindo mensagens...")
    producer = AvroProducer(
        {
            'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
            'schema.registry.url': SCHEMA_REGISTRY_URL
        },
        default_value_schema=USER_EVENT_SCHEMA
    )
    
    events = [
        {"user_id": 1, "username": "alice", "email": "alice@example.com", 
         "action": "LOGIN", "timestamp": int(time.time() * 1000),
         "metadata": {"ip": "192.168.1.1", "browser": "Chrome"}},
        {"user_id": 2, "username": "bob", "email": "bob@example.com",
         "action": "PURCHASE", "timestamp": int(time.time() * 1000),
         "metadata": {"product_id": "123", "price": "99.99"}},
        {"user_id": 3, "username": "charlie", "email": "charlie@example.com",
         "action": "VIEW", "timestamp": int(time.time() * 1000),
         "metadata": {"page": "/products", "duration": "30s"}},
        {"user_id": 1, "username": "alice", "email": "alice@example.com",
         "action": "LOGOUT", "timestamp": int(time.time() * 1000),
         "metadata": {"session_duration": "3600s"}},
        {"user_id": 4, "username": "diana", "email": "diana@example.com",
         "action": "LOGIN", "timestamp": int(time.time() * 1000),
         "metadata": {"ip": "192.168.1.2", "browser": "Firefox"}},
    ]
    
    for i, event in enumerate(events, 1):
        try:
            producer.produce(topic=TOPIC_NAME, value=event)
            print(f"  ✓ [{i}/{len(events)}] {event['username']} - {event['action']}")
            time.sleep(0.3)
        except Exception as e:
            print(f"  ✗ Erro na mensagem {i}: {e}")
    
    producer.flush()
    
    print("\n" + "=" * 60)
    print("✓ Concluído! Acesse:")
    print(f"  • Kafka UI: http://localhost:8080")
    print(f"  • AKHQ: http://localhost:8081")
    print("=" * 60)


if __name__ == "__main__":
    main()

