from confluent_kafka import Producer
import time

conf = {'bootstrap.servers': 'localhost:9092'}
producer = Producer(conf)
topic = 'demo-groups'

print(f"Produzindo 10.000 mensagens para '{topic}'...")

for i in range(10000):
    producer.produce(topic, value=f"Job-{i}")
    if i % 1000 == 0:
        producer.poll(0)
        print(f"Produzidas {i} mensagens...")

producer.flush()
print("Carga concluída!")


