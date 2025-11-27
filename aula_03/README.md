# Aula 2 - Kafka 101: Fundamentos e Arquitetura

Bem-vindo à aula prática de Apache Kafka! Aqui vamos explorar os conceitos fundamentais através de 5 demonstrações interativas.

## 📋 Agenda

1. **Fundamentos**: O que é Kafka, Log Distribuído e Event Streaming.
2. **Arquitetura**: Brokers, Zookeeper/KRaft, Tópicos e Partições.
3. **Mão na Massa**:
   - **Demo 1**: [Partições e Offsets](./demo_01_particoes_offsets/README.md)
   - **Demo 2**: [Replicação, ISR e Alta Disponibilidade](./demo_02_replicacao_falhas/README.md)
   - **Demo 3**: [Producers: Chaves vs Round-Robin](./demo_03_producers/README.md)
   - **Demo 4**: [Consumer Groups e Lag](./demo_04_consumer_groups_lag/README.md)
   - **Demo 5**: [Schema Registry e Avro](./demo_05_avro_schema_registry/README.md)

## 🛠️ Pré-requisitos

### 1. Ambiente Python
Usaremos um ambiente Conda unificado para todo o curso.
```bash
# Na raiz do projeto (Arq_Micro_MBA_Eng/)
conda env create -f environment.yml
conda activate arq-microsservicos-mba
```

### 2. Docker Cluster (Multi-Broker)
Para esta aula, precisamos de um cluster mais robusto com 3 brokers para testar falhas.
```bash
cd ../aula_01
docker-compose up -d
```
*Isso subirá: 3 Kafkas, Zookeeper, Schema Registry, Kafka UI, AKHQ e Postgres.*

### 3. Acesso às Ferramentas
- **Kafka UI**: [http://localhost:8080](http://localhost:8080) (Gestão visual do cluster)
- **AKHQ**: [http://localhost:8081](http://localhost:8081) (Alternativa para gestão)

## 🚀 Como Executar as Demos

Cada demo está em sua própria subpasta numerada. Siga a ordem sugerida na Agenda.
Dentro de cada pasta existe um `README.md` específico com o roteiro passo-a-passo.

Exemplo:
```bash
cd demo_01_particoes_offsets
# Siga as instruções do README local
```

## 🧹 Limpeza
Ao final da aula, para economizar recursos:
```bash
cd ../aula_01
docker-compose down
```

## ⚠️ Troubleshooting Comum

**Erro: "No brokers available"**
- Verifique se os containers estão rodando: `docker ps`
- Aguarde alguns segundos após o `docker-compose up`, o Kafka demora um pouco para estabilizar.

**Erro de Conexão no Python**
- Certifique-se de estar rodando os scripts de DENTRO da pasta da demo ou ajustando os caminhos.
- Confirme se o ambiente conda está ativo: `conda activate arq-microsservicos-mba`.


