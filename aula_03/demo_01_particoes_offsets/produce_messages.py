from confluent_kafka import Producer
import time

def delivery_report(err, msg):
    """ Chamado uma vez para cada mensagem produzida para indicar sucesso ou falha """
    if err is not None:
        print(f'Falha na entrega da mensagem: {err}')
    else:
        print(f'Mensagem "{msg.value().decode("utf-8")}" entregue na partição {msg.partition()} @ offset {msg.offset()}')

# Configuração do Producer
conf = {
    'bootstrap.servers': 'localhost:9092,localhost:9093,localhost:9094',
    'client.id': 'demo-producer-1'
}

producer = Producer(conf)

topic = 'demo-particoes'
print(f"Enviando 100 mensagens para o tópico '{topic}'...")

for i in range(100):
    message = f"Mensagem numero {i}"
    # O producer decide a partição (round-robin se não houver chave)
    producer.produce(topic, value=message, callback=delivery_report)
    producer.poll(0) # Serve para disparar os callbacks

# Espera todas as mensagens serem entregues
producer.flush()
print("Todas as mensagens foram enviadas!")


