# Demo 2: Replicação, ISR e Falhas

Esta demo mostra como o Kafka garante alta disponibilidade através da replicação e como ele lida com a falha de um broker.

## Conceitos Chave
- **Replication Factor (RF)**: Quantas cópias dos dados existem.
- **ISR (In-Sync Replicas)**: Réplicas que estão atualizadas com o líder.
- **Min Insync Replicas**: Mínimo de réplicas que devem confirmar a escrita para garantir durabilidade (acks=all).

## Roteiro

### 1. Preparar o Cenário
Crie um tópico com RF=3 e min.insync.replicas=2:
```bash
bash setup_topic.sh
```

### 2. Produção Contínua
Inicie um produtor que envia mensagens sem parar, para observarmos o fluxo durante a falha:
```bash
python continuous_producer.py
```
*Deixe este terminal rodando.*

### 3. Verificar ISR
Em outro terminal, verifique o estado atual das réplicas (ISR deve mostrar os 3 brokers):
```bash
bash check_isr.sh
```

### 4. Simular Falha
Vamos derrubar o broker `kafka-2`:
```bash
docker-compose stop kafka-2
```
*Observe o terminal do produtor: pode haver um breve erro ou pausa, mas ele deve continuar.*

Execute novamente o `check_isr.sh`. Você verá que o broker 2 saiu da lista de ISR. O Kafka elegeu um novo líder se o 2 fosse o líder.

### 5. Recuperação
Suba o broker novamente:
```bash
docker-compose start kafka-2
```
Aguarde alguns segundos e rode `check_isr.sh`. O broker 2 deve voltar para a lista de ISR após sincronizar os dados perdidos.


