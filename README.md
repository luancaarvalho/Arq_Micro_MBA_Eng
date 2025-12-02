# Arq_Micro_MBA_Eng

- Subir docker 
- Rodar script para criar conector
``` 
curl -X POST http://localhost:8083/connectors   -H "Content-Type: application/json"   -d '{
    "name": "postgres-source",
    "config": {
      "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
      "tasks.max": "1",

      "topic.prefix": "pgserver",

      "database.hostname": "postgres_source",
      "database.port": "5432",
      "database.user": "postgres",
      "database.password": "postgres",
      "database.dbname": "source_db",

      "plugin.name": "pgoutput",
      "slot.name": "debezium_slot",
      "publication.autocreate.mode": "filtered",

      "tombstones.on.delete": "false",

      "key.converter": "org.apache.kafka.connect.json.JsonConverter",
      "key.converter.schemas.enable": "false",

      "value.converter": "org.apache.kafka.connect.json.JsonConverter",
      "value.converter.schemas.enable": "false"
    }
  }'

```

- Logar no MINIO 
Username: admin
Password: admin123

- Criar tópico com nome "kafka-files"