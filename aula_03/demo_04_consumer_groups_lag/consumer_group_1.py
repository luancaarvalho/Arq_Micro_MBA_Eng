from confluent_kafka import Consumer

conf = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'demo-group', # Mesmo grupo do slow_consumer
    'auto.offset.reset': 'earliest'
}

consumer = Consumer(conf)
consumer.subscribe(['demo-groups'])

print("Consumidor RAPIDO 1 iniciado (ajudando o grupo)...")

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None: continue
        if msg.error(): continue

        # Processamento rápido
        print(f"🚀 Consumidor 1: {msg.value().decode()} | Partição {msg.partition()}")
except KeyboardInterrupt:
    pass
finally:
    consumer.close()


