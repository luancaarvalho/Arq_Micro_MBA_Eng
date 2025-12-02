from kafka import KafkaConsumer
import boto3
from datetime import datetime
import json
from kafka import KafkaAdminClient


KAFKA_BOOTSTRAP = "localhost:9094"
KAFKA_TOPIC = "pgserver.public.users"

consumer = KafkaConsumer(
    'pgserver.public.users',
    bootstrap_servers=KAFKA_BOOTSTRAP,
    auto_offset_reset="earliest",
    group_id="demo",
)

minio_client = boto3.client(
    "s3",
    endpoint_url="http://localhost:9000",
    aws_access_key_id="admin",
    aws_secret_access_key="admin123",
    region_name="us-east-1"
)

print("Consumindo mensagens do tópico...")

for msg in consumer:
    try:
        print('a')
        raw_value = msg.value
    
        filename = f"user_{datetime.utcnow().timestamp()}.txt"
    
        try:
            json_data = json.loads(raw_value)
            text_content = json.dumps(json_data, indent=2)
        except:
            text_content = raw_value 

        minio_client.put_object(
            Bucket="kafka-files",
            Key=filename,
            Body=text_content.encode("utf-8"),
            ContentType="text/plain"
        )
        
        print(f"✔ Arquivo enviado: {filename}")

    except Exception as e:
        print(f"Erro ao processar mensagem: {e}")
