#!/usr/bin/env python3
"""
Demonstra como funcionam Consumer Groups no Kafka.
Cria um tópico com 3 partitions e mostra rebalancing quando múltiplos consumers se conectam.
"""

import argparse
import time
import uuid
from confluent_kafka import Producer, Consumer
from confluent_kafka.admin import AdminClient, NewTopic, KafkaException

# Configurações
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "cg-demo"
CONSUMER_GROUP = "cg-demo"
NUM_PARTITIONS = 3


def _fmt_partitions(partitions):
    """Formata lista de partitions como p0,p1,..."""
    return ", ".join([f"p{tp.partition}" for tp in partitions]) if partitions else "nenhuma"


def _on_assign(consumer, partitions):
    """Callback exibido durante rebalancing quando partitions são atribuídas."""
    print(f"→ Rebalance: partitions ASSIGNED: {_fmt_partitions(partitions)}")


def _on_revoke(consumer, partitions):
    """Callback exibido durante rebalancing quando partitions são revogadas."""
    print(f"→ Rebalance: partitions REVOKED: {_fmt_partitions(partitions)}")


def create_topic():
    """Cria o tópico se não existir"""
    admin_client = AdminClient({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS
    })
    
    topic = NewTopic(TOPIC, num_partitions=NUM_PARTITIONS, replication_factor=1)
    
    print(f"Criando tópico: {TOPIC} com {NUM_PARTITIONS} partitions")
    futures = admin_client.create_topics([topic])
    
    for topic_name, future in futures.items():
        try:
            future.result()
            print(f"Tópico {topic_name} criado com sucesso")
        except Exception as e:
            error_str = str(e)
            if "TOPIC_ALREADY_EXISTS" in error_str or "already exists" in error_str.lower():
                print(f"Tópico {topic_name} já existe")
            else:
                raise


def produce_messages(num_messages=30):
    """Produz mensagens de exemplo no tópico"""
    producer = Producer({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS
    })
    
    print(f"\nProduzindo {num_messages} mensagens no tópico {TOPIC}...")
    
    for i in range(1, num_messages + 1):
        message = f"Mensagem {i:03d} - Timestamp: {int(time.time() * 1000)}"
        producer.produce(
            TOPIC,
            value=message.encode('utf-8'),
            key=f"key-{i % NUM_PARTITIONS}".encode('utf-8')  # Distribui entre partitions
        )
        producer.poll(0)
        
        if i % 10 == 0:
            print(f"  Enviadas {i} mensagens...")
    
    producer.flush()
    print(f"✓ {num_messages} mensagens enviadas com sucesso\n")


def consume_messages(consumer_id=None):
    """Consome mensagens do tópico usando consumer group"""
    if consumer_id is None:
        consumer_id = str(uuid.uuid4())[:8]
    
    consumer = Consumer({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': CONSUMER_GROUP,
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': True,
        'auto.commit.interval.ms': 1000
    })
    
    # Inscreve com callbacks para visualizar rebalancing ao vivo
    consumer.subscribe([TOPIC], on_assign=_on_assign, on_revoke=_on_revoke)
    
    print(f"=== Consumer ID: {consumer_id} ===")
    print(f"Consumer Group: {CONSUMER_GROUP}")
    print(f"Tópico: {TOPIC}")
    print(f"Aguardando mensagens... (Pressione Ctrl+C para sair)\n")
    
    try:
        message_count = 0
        while True:
            msg = consumer.poll(timeout=1.0)
            
            if msg is None:
                continue
            
            if msg.error():
                print(f"Erro: {msg.error()}")
                continue
            
            # Mostrar assignment atual (quais partitions este consumer está lendo)
            assignment = consumer.assignment()
            partitions = [f"p{tp.partition}" for tp in assignment]
            
            message_count += 1
            print(
                f"[#{message_count:05d} | Consumer {consumer_id}] "
                f"Partition: {msg.partition()} | "
                f"Offset: {msg.offset()} | "
                f"Assignment: {', '.join(partitions) if partitions else 'nenhuma'} | "
                f"Mensagem: {msg.value().decode('utf-8')}"
            )
    
    except KeyboardInterrupt:
        print(f"\n\nConsumer {consumer_id} finalizado")
        print(f"Mensagens consumidas nesta sessão: {message_count}")
    finally:
        consumer.close()


def main():
    parser = argparse.ArgumentParser(
        description="Demonstra Consumer Groups no Kafka"
    )
    parser.add_argument(
        '--produce',
        action='store_true',
        help='Produz mensagens de exemplo no tópico'
    )
    parser.add_argument(
        '--consumer-id',
        type=str,
        default=None,
        help='ID único para este consumer (útil para rodar múltiplas instâncias)'
    )
    
    args = parser.parse_args()
    
    # Criar tópico
    create_topic()
    
    if args.produce:
        produce_messages()
    else:
        consume_messages(args.consumer_id)


if __name__ == "__main__":
    main()

