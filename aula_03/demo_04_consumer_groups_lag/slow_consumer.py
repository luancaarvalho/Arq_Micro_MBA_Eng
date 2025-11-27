from confluent_kafka import Consumer
import time

conf = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'demo-group',
    'auto.offset.reset': 'earliest'
}

consumer = Consumer(conf)
consumer.subscribe(['demo-groups'])

print("Consumidor LENTO iniciado (group: demo-group)...")

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None: continue
        if msg.error():
            print(f"Erro: {msg.error()}")
            continue

        print(f"Processando {msg.value().decode()} | Partição {msg.partition()}")
        time.sleep(0.1) # Simula processamento lento (10 msg/s)
except KeyboardInterrupt:
    pass
finally:
    consumer.close()


