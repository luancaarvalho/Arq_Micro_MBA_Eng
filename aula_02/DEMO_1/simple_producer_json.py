#!/usr/bin/env python3
"""
Script simples para produzir mensagens JSON no Kafka e registrar schema
Execute: python simple_producer_json.py
"""

import json
import time
import requests
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka import Producer

# Configurações
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
SCHEMA_REGISTRY_URL = "http://localhost:8082"
TOPIC_NAME = "user-events"

# Schema JSON para registro no Schema Registry
USER_EVENT_SCHEMA = {
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
}


def register_schema():
    """Registra o schema no Schema Registry via API REST"""
    print("\n[2/3] Registrando schema no Schema Registry...")
    
    url = f"{SCHEMA_REGISTRY_URL}/subjects/{TOPIC_NAME}-value/versions"
    headers = {"Content-Type": "application/vnd.schemaregistry.v1+json"}
    payload = {"schema": json.dumps(USER_EVENT_SCHEMA)}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            schema_id = response.json().get("id")
            print(f"  ✓ Schema registrado! (ID: {schema_id})")
        elif response.status_code == 409:
            # Schema já existe, obtém o ID
            get_url = f"{SCHEMA_REGISTRY_URL}/subjects/{TOPIC_NAME}-value/versions/latest"
            response = requests.get(get_url)
            if response.status_code == 200:
                schema_id = response.json().get("id")
                print(f"  ✓ Schema já existe! (ID: {schema_id})")
        else:
            print(f"  ⚠ Resposta do Schema Registry: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"  ⚠ Erro ao registrar schema: {e}")


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
    register_schema()
    
    # 3. Produzir mensagens
    print("\n[3/3] Produzindo mensagens...")
    producer = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})
    
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
            producer.produce(
                TOPIC_NAME,
                value=json.dumps(event).encode('utf-8')
            )
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

