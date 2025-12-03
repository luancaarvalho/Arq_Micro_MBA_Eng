#!/usr/bin/env python3
"""
Consumidor simples e contínuo: lê mensagens do tópico Debezium e grava objetos JSON no MinIO
Se a variável de ambiente `KAFKA_TO_MINIO_MAX_MESSAGES` estiver definida e >0, o consumidor
encerra após esse número de mensagens (útil para testes). Caso contrário roda continuamente.
"""

import json
import time
from kafka import KafkaConsumer
from minio import Minio
from minio.error import S3Error
from datetime import datetime
from io import BytesIO
import os

# Config
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_TOPIC = os.environ.get('KAFKA_TOPIC', 'cdc-source-server.public.products')

MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT', 'localhost:9000')
MINIO_ACCESS_KEY = os.environ.get('MINIO_ACCESS_KEY', 'minioadmin')
MINIO_SECRET_KEY = os.environ.get('MINIO_SECRET_KEY', 'minioadmin')
MINIO_BUCKET = os.environ.get('MINIO_BUCKET', 'cdc-data')

# Quantas mensagens processar antes de sair (0 = infinito)
MAX_MESSAGES = int(os.environ.get('KAFKA_TO_MINIO_MAX_MESSAGES', '0'))


def ensure_bucket(client: Minio, bucket: str):
    try:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
    except S3Error as e:
        print(f"Erro ao verificar/criar bucket: {e}")
        raise


def main():
    print("🔌 Conectando ao MinIO...")
    client = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False)
    ensure_bucket(client, MINIO_BUCKET)
    print("✅ MinIO pronto")

    print(f"📥 Conectando ao Kafka (tópico: {KAFKA_TOPIC})...")
    group_id = os.environ.get('KAFKA_TO_MINIO_GROUP', f'kafka-to-minio-{int(time.time())}')
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id=group_id,
        value_deserializer=lambda m: m
    )

    print("✅ Consumer criado")

    count = 0
    try:
        for message in consumer:
            try:
                if message.value is None:
                    continue
                if isinstance(message.value, bytes):
                    data = json.loads(message.value.decode('utf-8'))
                else:
                    data = json.loads(message.value)
            except Exception:
                data = {"raw": str(message.value)}

            ts = datetime.utcnow().strftime('%Y%m%dT%H%M%S%f')
            fname = f"product_msg_{ts}_{message.partition}_{message.offset}.json"
            content = json.dumps(data, ensure_ascii=False).encode('utf-8')

            object_name = f"messages/{datetime.utcnow().strftime('%Y/%m/%d')}/{fname}"
            bio = BytesIO(content)
            client.put_object(MINIO_BUCKET, object_name, bio, length=len(content), content_type='application/json')

            print(f"📤 Enviado: {object_name}")
            count += 1

            if MAX_MESSAGES and count >= MAX_MESSAGES:
                print(f"🎯 Alcançado MAX_MESSAGES={MAX_MESSAGES}, finalizando")
                break

    except KeyboardInterrupt:
        print("⏹️ Interrompido pelo usuário")
    finally:
        consumer.close()


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
Consumidor simples: lê mensagens do tópico Debezium e grava objetos JSON no MinIO
Usa: kafka-python + minio

Ele processa até `MAX_MESSAGES` mensagens e fecha, para uso rápido em validação.
"""

import json
import time
from kafka import KafkaConsumer
from minio import Minio
from minio.error import S3Error
from datetime import datetime
import os

# Config
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
KAFKA_TOPIC = 'cdc-source-server.public.products'

MINIO_ENDPOINT = 'localhost:9000'
MINIO_ACCESS_KEY = 'minioadmin'
MINIO_SECRET_KEY = 'minioadmin'
MINIO_BUCKET = 'cdc-data'

# Quantas mensagens processar antes de sair (0 = infinito)
MAX_MESSAGES = 20


def ensure_bucket(client: Minio, bucket: str):
    try:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
    except S3Error as e:
        print(f"Erro ao verificar/criar bucket: {e}")
        raise


def main():
    print("🔌 Conectando ao MinIO...")
    client = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False)
    ensure_bucket(client, MINIO_BUCKET)
    print("✅ MinIO pronto")

    print(f"📥 Conectando ao Kafka (tópico: {KAFKA_TOPIC})...")
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='kafka-to-minio',
        value_deserializer=lambda m: m
    )

    print("✅ Consumer criado")

    count = 0
    try:
        for message in consumer:
            # message.value pode ser bytes com JSON
            try:
                if message.value is None:
                    continue
                if isinstance(message.value, bytes):
                    data = json.loads(message.value.decode('utf-8'))
                else:
                    data = json.loads(message.value)
            except Exception as e:
                # fallback: guardar string
                data = {"raw": str(message.value)}

            # filename com timestamp e offset
            ts = datetime.utcnow().strftime('%Y%m%dT%H%M%S%f')
            fname = f"product_msg_{ts}_{message.partition}_{message.offset}.json"
            content = json.dumps(data, ensure_ascii=False).encode('utf-8')

            # colocar em bucket
            object_name = f"messages/{datetime.utcnow().strftime('%Y/%m/%d')}/{fname}"
            # usar sempre um stream (compatível com diferentes versões da lib)
            from io import BytesIO
            bio = BytesIO(content)
            client.put_object(MINIO_BUCKET, object_name, bio, length=len(content), content_type='application/json')

            print(f"📤 Enviado: {object_name}")
            count += 1

            if MAX_MESSAGES and count >= MAX_MESSAGES:
                print(f"🎯 Alcançado MAX_MESSAGES={MAX_MESSAGES}, finalizando")
                break

    except KeyboardInterrupt:
        print("⏹️ Interrompido pelo usuário")
    finally:
        consumer.close()


if __name__ == '__main__':
    main()
