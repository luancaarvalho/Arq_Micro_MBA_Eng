#!/usr/bin/env python3
"""
Demonstra como funcionam Offsets no Kafka.
Mostra como criar novos consumer groups e como fazer seek para ler do início.
"""

import argparse
import time
import uuid
from confluent_kafka import Producer, Consumer
from confluent_kafka.admin import AdminClient, NewTopic, KafkaException

# Configurações
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "offset-demo"
DEFAULT_CONSUMER_GROUP = "offset-demo-default"


def _fmt_partitions(partitions):
    """Formata lista de partitions como p0,p1,..."""
    return ", ".join([f"p{tp.partition}" for tp in partitions]) if partitions else "nenhuma"


def _on_assign(consumer, partitions):
    """Callback exibido quando partitions são atribuídas (rebalancing)."""
    try:
        infos = []
        for tp in partitions:
            low, high = consumer.get_watermark_offsets(tp, timeout=5)
            committed = consumer.committed([tp], timeout=5)[0].offset
            infos.append(
                f"p{tp.partition} [low={low}, high={high}) committed={committed}"
            )
        print("→ Assign recebido: " + "; ".join(infos))
    except Exception as e:
        print(f"→ Assign recebido (detalhes indisponíveis): {e}")


def _on_revoke(consumer, partitions):
    """Callback exibido quando partitions são revogadas (rebalancing)."""
    print(f"→ Revoke recebido: {_fmt_partitions(partitions)}")


def create_topic():
    """Cria o tópico se não existir"""
    admin_client = AdminClient({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS
    })
    
    topic = NewTopic(TOPIC, num_partitions=1, replication_factor=1)
    
    print(f"Criando tópico: {TOPIC}")
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


def produce_messages(num_messages=10):
    """Produz mensagens de exemplo no tópico"""
    producer = Producer({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS
    })
    
    print(f"\nProduzindo {num_messages} mensagens no tópico {TOPIC}...")
    
    messages = [
        "Mensagem inicial - Offset 0",
        "Segunda mensagem - Offset 1",
        "Terceira mensagem - Offset 2",
        "Quarta mensagem - Offset 3",
        "Quinta mensagem - Offset 4",
        "Sexta mensagem - Offset 5",
        "Sétima mensagem - Offset 6",
        "Oitava mensagem - Offset 7",
        "Nona mensagem - Offset 8",
        "Última mensagem - Offset 9"
    ]
    
    for i, msg_text in enumerate(messages[:num_messages]):
        producer.produce(
            TOPIC,
            value=msg_text.encode('utf-8'),
            key=f"key-{i}".encode('utf-8')
        )
        producer.poll(0)
        print(f"  [{i}] {msg_text}")
    
    producer.flush()
    print(f"\n✓ {num_messages} mensagens enviadas com sucesso\n")


def consume_messages(group_id, seek_beginning=False):
    """Consome mensagens do tópico"""
    consumer = Consumer({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': group_id,
        'auto.offset.reset': 'earliest' if not seek_beginning else 'earliest',
        'enable.auto.commit': True,
        'auto.commit.interval.ms': 1000
    })
    
    # Inscreve com callbacks para visualizar rebalancing ao vivo
    consumer.subscribe([TOPIC], on_assign=_on_assign, on_revoke=_on_revoke)
    
    print(f"=== Consumer Group: {group_id} ===")
    print(f"Tópico: {TOPIC}")
    
    if seek_beginning:
        print("Modo: SEEK BEGINNING (lendo do offset 0, ignorando offsets salvos)")
    else:
        print("Modo: Normal (respeitando offsets do consumer group)")
    
    print("Aguardando mensagens... (Pressione Ctrl+C para sair)\n")
    
    try:
        # Se seek_beginning, aguardar assignment e fazer seek
        if seek_beginning:
            # Aguardar assignment
            assignment = None
            timeout = 10
            start = time.time()
            while assignment is None and (time.time() - start) < timeout:
                msg = consumer.poll(timeout=1.0)
                assignment = consumer.assignment()
                if assignment:
                    break
            
            if assignment:
                # Fazer seek para o início (offset 0)
                for tp in assignment:
                    consumer.seek(tp, 0)
                    print(f"✓ Seek para partition {tp.partition}, offset 0")
                # Exibir watermarks após seek
                for tp in assignment:
                    low, high = consumer.get_watermark_offsets(tp, timeout=5)
                    committed = consumer.committed([tp], timeout=5)[0].offset
                    print(f"  Watermarks p{tp.partition}: low={low}, high={high} | committed={committed}")
                print()
            else:
                print("⚠ Não foi possível obter assignment")
        
        message_count = 0
        
        while True:
            msg = consumer.poll(timeout=1.0)
            
            if msg is None:
                if message_count == 0:
                    continue
                else:
                    print("\n✓ Todas as mensagens foram lidas")
                    break
            
            if msg.error():
                print(f"Erro: {msg.error()}")
                continue
            
            message_count += 1
            print(
                f"[{message_count}] "
                f"Partition: {msg.partition()} | "
                f"Offset: {msg.offset()} | "
                f"Mensagem: {msg.value().decode('utf-8')}"
            )
    
    except KeyboardInterrupt:
        print(f"\n\nConsumer finalizado")
        print(f"Mensagens consumidas nesta sessão: {message_count}")
    finally:
        consumer.close()


def main():
    parser = argparse.ArgumentParser(
        description="Demonstra Offsets no Kafka"
    )
    parser.add_argument(
        '--produce',
        action='store_true',
        help='Produz mensagens de exemplo no tópico'
    )
    parser.add_argument(
        '--new-group',
        action='store_true',
        help='Usa um novo consumer group único (lê do início)'
    )
    parser.add_argument(
        '--seek-beginning',
        action='store_true',
        help='Faz seek para offset 0, ignorando offsets salvos'
    )
    
    args = parser.parse_args()
    
    # Criar tópico
    create_topic()
    
    if args.produce:
        produce_messages()
    else:
        # Determinar consumer group
        if args.new_group:
            group_id = f"offset-demo-{uuid.uuid4().hex[:8]}"
            print(f"Usando novo consumer group: {group_id}\n")
        else:
            group_id = DEFAULT_CONSUMER_GROUP
        
        consume_messages(group_id, args.seek_beginning)


if __name__ == "__main__":
    main()

