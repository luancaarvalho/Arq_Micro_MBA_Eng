# Demo 1: Partições e Offsets

Esta demo explora a estrutura básica de um tópico no Kafka: partições, replicação e offsets.

## O que você vai ver
1. Criação de um tópico com 4 partições e fator de replicação 3.
2. Produção de mensagens simples.
3. Inspeção visual via Kafka UI e linha de comando.
4. Verificação de que as mensagens são distribuídas entre partições.

## Passo a Passo

### 0. Preparar Ambiente Conda
Primeiro, crie o ambiente conda unificado do curso:
```bash
# Na raiz do projeto (Arq_Micro_MBA_Eng/)
conda env create -f environment.yml
conda activate arq-microsservicos-mba
```

**Dependências necessárias:**
- `confluent-kafka[avro]>=2.3.0` - Cliente Kafka
- Python 3.11

### 1. Preparação Docker
Certifique-se que o ambiente Docker está rodando:
```bash
cd ../../aula_01
docker compose up -d
```
(Acesse `http://localhost:8080` para abrir o Kafka UI)

### 2. Criar o Tópico
Execute o script para criar o tópico `demo-particoes`:
```bash
bash create_topic.sh
```
*Vá ao Kafka UI > Topics e veja o tópico `demo-particoes` com 4 partições.*

### 3. Produzir Mensagens
Execute o script Python para enviar 100 mensagens:
```bash
python produce_messages.py
```
*Observe no console que as mensagens são enviadas para diferentes partições.*

### 4. Inspecionar Offsets
Use o script abaixo para ler as mensagens e ver os offsets:
```bash
bash inspect_offsets.sh
```
*Note que os offsets são sequenciais **dentro de cada partição**, mas não há ordem global.*


