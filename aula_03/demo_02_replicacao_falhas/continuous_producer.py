from confluent_kafka import Producer
import time
import socket

conf = {
    'bootstrap.servers': 'localhost:9092,localhost:9093,localhost:9094',
    'client.id': 'resilient-producer',
    'acks': 'all',  # Garante durabilidade máxima
    'retries': 5,   # Tenta reenviar em caso de falha temporária
    'retry.backoff.ms': 500
}

producer = Producer(conf)
topic = 'demo-replicacao'

def acked(err, msg):
    if err is not None:
        print(f"❌ Falha: {err}")
    else:
        print(f"✅ Enviado: {msg.value().decode('utf-8')} | Partição: {msg.partition()}")

print("Iniciando produção contínua. Pressione Ctrl+C para parar.")
count = 0

try:
    while True:
        msg = f"Evento critico #{count}"
        try:
            producer.produce(topic, value=msg, callback=acked)
            producer.poll(0)
        except BufferError:
            print("Buffer cheio, aguardando...")
            producer.poll(1)
        
        count += 1
        time.sleep(1) # 1 mensagem por segundo

except KeyboardInterrupt:
    print("Parando...")
finally:
    producer.flush()


