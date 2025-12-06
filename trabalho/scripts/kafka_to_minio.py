import json
import time
from confluent_kafka import Consumer
from minio import Minio
from datetime import datetime, timezone
from io import BytesIO
import os

# Kafka settings
KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", "cdc-source-server.public.products")

# MinIO settings
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "cdc-data")

# Optional limit for debugging
MAX_MESSAGES = int(os.environ.get("KAFKA_TO_MINIO_MAX_MESSAGES", "0"))


def ensure_bucket(client, bucket):
    """Cria o bucket se não existir."""
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)


def utc_timestamp():
    """Timestamp seguro e sem warnings."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")


def utc_path():
    """Diretório por data (ano/mês/dia) em UTC."""
    return datetime.now(timezone.utc).strftime("%Y/%m/%d")


def main():
    print("🚀 Conectando ao MinIO...")
    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False,
    )
    ensure_bucket(client, MINIO_BUCKET)
    print("MinIO pronto ✔️")

    print(f"Conectando ao Kafka ({KAFKA_BOOTSTRAP_SERVERS})...")

    consumer = Consumer(
        {
            "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
            "group.id": f"kafka-to-minio-{int(time.time())}",
            "auto.offset.reset": "earliest",
        }
    )

    consumer.subscribe([KAFKA_TOPIC])
    print(f"Consumer inscrito no tópico: {KAFKA_TOPIC}")

    count = 0

    while True:
        msg = consumer.poll(1.0)

        if msg is None:
            continue  # timeout, sem mensagens

        if msg.error():
            print("⚠️ Erro no Kafka:", msg.error())
            continue

        value = msg.value()

        # Tombstone ou heartbeat → ignorar
        if value is None:
            print("⚪ Mensagem vazia (tombstone/heartbeat) ignorada.")
            continue

        # Decodificação segura
        try:
            data = json.loads(value.decode("utf-8"))
        except Exception:
            data = {"raw": value.decode("utf-8", errors="ignore")}

        # Nome do arquivo e path em UTC
        filename = (
            f"product_msg_{utc_timestamp()}_{msg.partition()}_{msg.offset()}.json"
        )
        object_name = f"messages/{utc_path()}/{filename}"

        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")

        client.put_object(
            MINIO_BUCKET,
            object_name,
            BytesIO(payload),
            len(payload),
            content_type="application/json",
        )

        print(f"📦 Enviado para MinIO → {object_name}")

        count += 1

        if MAX_MESSAGES and count >= MAX_MESSAGES:
            print("🔚 Limite MAX_MESSAGES atingido, encerrando.")
            break

    consumer.close()


if __name__ == "__main__":
    main()
