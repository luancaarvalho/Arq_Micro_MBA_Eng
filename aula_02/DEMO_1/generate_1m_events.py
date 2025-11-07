import json
import time
import argparse
import signal
import sys
import multiprocessing
from pathlib import Path
from faker import Faker
from confluent_kafka import Producer, Consumer, TopicPartition
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka import KafkaException
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import SerializationContext, MessageField

# Configurações
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
SCHEMA_REGISTRY_URL = "http://localhost:8082"
TOPIC_JSON = "orders-json"
TOPIC_AVRO = "orders-avro"
SCHEMA_FILE = Path(__file__).parent / "schema.avsc"

# Constantes
DEFAULT_TARGET_EVENTS = 1_000_000  # 1 milhão de eventos

# Número de workers e partitions baseado em CPUs disponíveis
NUM_WORKERS = multiprocessing.cpu_count()

running = True


def signal_handler(sig, frame):
    """Handler para Ctrl+C"""
    global running
    print("\n\nInterrompendo geração...")
    running = False


signal.signal(signal.SIGINT, signal_handler)


def load_avro_schema():
    """Carrega o schema Avro do arquivo"""
    with open(SCHEMA_FILE, 'r') as f:
        return f.read()


def get_topic_message_count(topic_name):
    """Obtém o número total de mensagens em um tópico"""
    admin_client = AdminClient({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS
    })
    
    try:
        # Obter metadados do tópico
        metadata = admin_client.list_topics(timeout=10)
        if topic_name not in metadata.topics:
            return None
        
        topic_metadata = metadata.topics[topic_name]
        total_messages = 0
        
        # Para cada partição, obter o high watermark (último offset + 1)
        # Usar um consumer para obter os offsets reais
        consumer = Consumer({
            'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
            'group.id': f'temp-count-{topic_name}',
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False
        })
        
        # Obter partições do tópico
        partitions = []
        for partition_id in topic_metadata.partitions:
            partitions.append(TopicPartition(topic_name, partition_id))
        
        if not partitions:
            consumer.close()
            return None
        
        # Obter offsets baixo e alto para cada partição
        total_messages = 0
        for partition in partitions:
            try:
                low, high = consumer.get_watermark_offsets(partition, timeout=5)
                total_messages += (high - low)
            except Exception as e:
                print(f"Erro ao obter offset da partição {partition.partition}: {e}")
        
        consumer.close()
        return total_messages
        
    except Exception as e:
        print(f"Erro ao obter contagem de mensagens do tópico {topic_name}: {e}")
        return None


def create_topics():
    """Deleta e recria os tópicos com o número correto de partitions"""
    admin_client = AdminClient({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS
    })
    
    # Primeiro, deletar tópicos existentes
    topics_to_delete = [TOPIC_JSON, TOPIC_AVRO]
    print(f"Deletando tópicos existentes (se houver): {', '.join(topics_to_delete)}")
    
    try:
        delete_futures = admin_client.delete_topics(topics_to_delete, operation_timeout=30)
        for topic, future in delete_futures.items():
            try:
                future.result()
                print(f"  ✓ Tópico {topic} deletado")
            except Exception as e:
                if "UNKNOWN_TOPIC_OR_PARTITION" in str(e):
                    print(f"  - Tópico {topic} não existia")
                else:
                    print(f"  ! Erro ao deletar {topic}: {e}")
        
        # Aguardar um pouco para garantir que os tópicos foram deletados
        time.sleep(2)
    except Exception as e:
        print(f"Erro ao deletar tópicos: {e}")
    
    # Criar tópicos com múltiplas partitions para paralelização
    topics = [
        NewTopic(TOPIC_JSON, num_partitions=NUM_WORKERS, replication_factor=1),
        NewTopic(TOPIC_AVRO, num_partitions=NUM_WORKERS, replication_factor=1)
    ]
    
    print(f"\nCriando tópicos: {TOPIC_JSON}, {TOPIC_AVRO} (com {NUM_WORKERS} partitions cada)")
    futures = admin_client.create_topics(topics)
    
    for topic, future in futures.items():
        try:
            future.result()
            print(f"  ✓ Tópico {topic} criado com {NUM_WORKERS} partitions")
        except Exception as e:
            error_str = str(e)
            if "TOPIC_ALREADY_EXISTS" in error_str or "already exists" in error_str.lower():
                print(f"  ! AVISO: Tópico {topic} ainda existe (pode ter 1 partition)")
            else:
                raise


def generate_order():
    """Gera um evento Order usando Faker"""
    fake = Faker()
    return {
        "id": fake.uuid4(),
        "user_id": fake.uuid4(),
        "user_email": fake.email(),
        "user_name": fake.name(),
        "total": round(fake.pyfloat(left_digits=3, right_digits=2, positive=True), 2),
        "currency": fake.currency_code(),
        "items_count": fake.random_int(min=1, max=50),
        "payment_method": fake.random_element(elements=("credit_card", "debit_card", "paypal", "bank_transfer")),
        "shipping_address": fake.address().replace('\n', ', '),
        "created_at": int(time.time() * 1000)
    }


def delivery_callback(err, msg):
    """Callback para verificar se a mensagem foi entregue com sucesso"""
    if err is not None:
        raise KafkaException(f"Falha ao publicar mensagem: {err}")


def worker_producer(worker_id, target_events_per_worker, avro_schema_str, queue):
    """Worker que produz mensagens em paralelo"""
    # Cada worker cria seus próprios producers e serializers
    producer_config = {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'compression.type': 'none',
        'acks': '1',
        'linger.ms': 100,  # Otimização de batch
        'batch.num.messages': 10000,  # Batch de 10k mensagens
    }
    
    producer_json = Producer(producer_config)
    
    # Schema Registry client e serializer para este worker
    schema_registry_client = SchemaRegistryClient({'url': SCHEMA_REGISTRY_URL})
    avro_serializer = AvroSerializer(
        schema_registry_client,
        avro_schema_str,
        lambda obj, ctx: obj
    )
    producer_avro = Producer(producer_config)
    
    total_bytes = 0
    total_messages_json = 0
    total_messages_avro = 0
    
    # Cada worker produz para sua própria partition
    partition = worker_id % NUM_WORKERS
    
    try:
        while total_messages_json < target_events_per_worker:
            # Gerar evento
            order = generate_order()
            
            # Serializar JSON
            json_str = json.dumps(order, ensure_ascii=False)
            json_bytes = len(json_str.encode('utf-8'))
            
            # Tentar publicar ambas as mensagens
            json_published = False
            avro_published = False
            
            # Publicar JSON
            try:
                producer_json.produce(
                    TOPIC_JSON,
                    json_str.encode('utf-8'),
                    callback=delivery_callback
                )
                json_published = True
            except Exception as e:
                print(f"Worker {worker_id}: Erro ao publicar JSON: {e}")
                producer_json.poll(0)  # Processar erros pendentes
            
            # Serializar e publicar Avro
            try:
                serialization_context = SerializationContext(TOPIC_AVRO, MessageField.VALUE)
                avro_bytes = avro_serializer(order, serialization_context)
                producer_avro.produce(
                    TOPIC_AVRO,
                    avro_bytes,
                    callback=delivery_callback
                )
                avro_published = True
            except Exception as e:
                print(f"Worker {worker_id}: Erro ao publicar Avro: {e}")
                producer_avro.poll(0)  # Processar erros pendentes
            
            # Só contar se AMBAS as publicações foram bem-sucedidas
            if json_published and avro_published:
                total_messages_json += 1
                total_messages_avro += 1
                total_bytes += json_bytes
            else:
                # Se uma falhou, fazer poll para processar erros e continuar
                producer_json.poll(0)
                producer_avro.poll(0)
            
            # Poll periodicamente para processar callbacks
            if (total_messages_json + total_messages_avro) % 1000 == 0:
                producer_json.poll(0)
                producer_avro.poll(0)
    
    except KeyboardInterrupt:
        pass
    finally:
        # Garantir que todas as mensagens sejam enviadas
        producer_json.flush()
        producer_avro.flush()
    
    # Validar que ambos têm o mesmo número de mensagens
    if total_messages_json != total_messages_avro:
        print(f"⚠️  AVISO Worker {worker_id}: JSON={total_messages_json}, Avro={total_messages_avro}")
    
    queue.put((total_messages_json, total_messages_avro, total_bytes))


def main():
    parser = argparse.ArgumentParser(description="Gera eventos JSON e Avro para comparação de tamanho")
    parser.add_argument(
        "--target-events",
        type=int,
        default=DEFAULT_TARGET_EVENTS,
        help=f"Número de eventos alvo (padrão: {DEFAULT_TARGET_EVENTS:,})"
    )
    args = parser.parse_args()
    
    target_events = args.target_events
    
    print(f"=== Gerador de Eventos Kafka (Paralelizado) ===")
    print(f"Tópico JSON: {TOPIC_JSON}")
    print(f"Tópico Avro: {TOPIC_AVRO}")
    print(f"Número de eventos alvo: {target_events:,}")
    print(f"Schema Registry: {SCHEMA_REGISTRY_URL}")
    print(f"Workers: {NUM_WORKERS}")
    print()
    
    # Criar tópicos
    create_topics()
    
    # Carregar schema Avro
    avro_schema_str = load_avro_schema()
    
    # Calcular eventos por worker
    target_events_per_worker = target_events // NUM_WORKERS
    
    print(f"Iniciando {NUM_WORKERS} workers paralelos...")
    print("Pressione Ctrl+C para parar\n")
    
    start_time = time.time()
    
    # Criar processos workers
    processes = []
    queue = multiprocessing.Queue()
    
    try:
        for i in range(NUM_WORKERS):
            p = multiprocessing.Process(
                target=worker_producer,
                args=(i, target_events_per_worker, avro_schema_str, queue)
            )
            p.start()
            processes.append(p)
        
        # Monitorar progresso
        last_log_time = start_time
        completed_workers = 0
        
        while completed_workers < NUM_WORKERS:
            # Verificar se algum processo terminou
            for p in processes:
                if not p.is_alive():
                    completed_workers += 1
            
            # Log de progresso a cada 5 segundos
            current_time = time.time()
            if current_time - last_log_time >= 5.0:
                elapsed = current_time - start_time
                print(f"Workers ativos: {NUM_WORKERS - completed_workers}/{NUM_WORKERS} | Tempo: {elapsed:.1f}s")
                last_log_time = current_time
            
            time.sleep(0.5)
        
        # Aguardar todos os processos terminarem
        for p in processes:
            p.join()
    
    except KeyboardInterrupt:
        print("\nInterrompendo workers...")
        for p in processes:
            p.terminate()
        for p in processes:
            p.join()
    
    # Coletar resultados
    total_messages_json = 0
    total_messages_avro = 0
    total_bytes = 0
    
    while not queue.empty():
        msgs_json, msgs_avro, bytes_count = queue.get()
        total_messages_json += msgs_json
        total_messages_avro += msgs_avro
        total_bytes += bytes_count
    
    elapsed_time = time.time() - start_time
    
    # Calcular tamanhos para comparação de storage
    GB = 1024 * 1024 * 1024
    final_gb = total_bytes / GB if total_bytes > 0 else 0
    
    print("\n=== Estatísticas Finais ===")
    print(f"Mensagens JSON geradas: {total_messages_json:,}")
    print(f"Mensagens Avro geradas: {total_messages_avro:,}")
    print(f"Tamanho total JSON: {final_gb:.2f} GB ({total_bytes:,} bytes)")
    print(f"Tempo total: {elapsed_time:.2f} segundos")
    if total_messages_json > 0:
        print(f"Velocidade: {total_messages_json / elapsed_time:.0f} eventos/segundo")
    if total_bytes > 0:
        print(f"Velocidade média: {(total_bytes / elapsed_time) / (1024 * 1024):.2f} MB/s")
    
    # VALIDAÇÃO: Verificar se ambos os tópicos têm o mesmo número de mensagens
    print("\n=== Validação de Consistência ===")
    if total_messages_json == total_messages_avro:
        print(f"✓ SUCESSO: Ambos os tópicos têm {total_messages_json:,} mensagens")
    else:
        print(f"✗ ERRO: Número de mensagens diferente!")
        print(f"  JSON: {total_messages_json:,}")
        print(f"  Avro: {total_messages_avro:,}")
        print(f"  Diferença: {abs(total_messages_json - total_messages_avro):,}")
    
    # Validar contagem real nos tópicos Kafka (aguardar um pouco para garantir que todas as mensagens foram commitadas)
    print("\nAguardando 5 segundos para garantir que todas as mensagens foram commitadas...")
    time.sleep(5)
    
    print("Validando contagem real nos tópicos Kafka...")
    count_json = get_topic_message_count(TOPIC_JSON)
    count_avro = get_topic_message_count(TOPIC_AVRO)
    
    if count_json is not None and count_avro is not None:
        print(f"  Tópico {TOPIC_JSON}: {count_json:,} mensagens")
        print(f"  Tópico {TOPIC_AVRO}: {count_avro:,} mensagens")
        
        if count_json == count_avro:
            print(f"✓ VALIDAÇÃO FINAL: Ambos os tópicos têm {count_json:,} mensagens no Kafka")
        else:
            print(f"✗ VALIDAÇÃO FALHOU: Número de mensagens diferente nos tópicos!")
            print(f"  Diferença: {abs(count_json - count_avro):,}")
    else:
        print("  Não foi possível validar a contagem real nos tópicos")
    
    print(f"\nTópicos criados:")
    print(f"  - {TOPIC_JSON} ({NUM_WORKERS} partitions)")
    print(f"  - {TOPIC_AVRO} ({NUM_WORKERS} partitions)")
    print(f"\nUse o comando abaixo para medir o tamanho em disco:")
    print(f"  docker exec kafka bash -c 'du -sh /var/lib/kafka/data/{TOPIC_JSON}-* /var/lib/kafka/data/{TOPIC_AVRO}-*'")


if __name__ == "__main__":
    main()
