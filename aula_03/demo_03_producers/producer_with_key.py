from confluent_kafka import Producer
import time

conf = {'bootstrap.servers': 'localhost:9092'}
producer = Producer(conf)
topic = 'demo-producers'

def acked(err, msg):
    if not err:
        print(f"SKEY: {msg.key().decode()} -> Partição {msg.partition()}")

users = ['user_123', 'user_456', 'user_789', 'user_000']

print(f"Produzindo mensagens com CHAVE para '{topic}'...")

# Envia 5 mensagens para cada usuário
for _ in range(5):
    for user_id in users:
        producer.produce(topic, key=user_id, value=f"Evento do {user_id}", callback=acked)
    
    producer.poll(0)
    time.sleep(0.5)

producer.flush()
print("Concluído. Note que cada user_id sempre caiu na mesma partição.")


