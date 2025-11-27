from confluent_kafka import Producer
import time

conf = {'bootstrap.servers': 'localhost:9092'}
producer = Producer(conf)
topic = 'demo-producers'

def acked(err, msg):
    if not err:
        print(f"NO-KEY -> Partição {msg.partition()}")

print(f"Produzindo mensagens SEM chave para '{topic}' (Round-Robin)...")

for i in range(20):
    producer.produce(topic, value=f"Mensagem {i}", callback=acked)
    producer.poll(0)
    time.sleep(0.2)

producer.flush()
print("Concluído. As mensagens devem estar espalhadas entre as partições.")


