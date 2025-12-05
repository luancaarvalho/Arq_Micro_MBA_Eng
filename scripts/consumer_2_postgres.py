from kafka import KafkaConsumer
import psycopg
import json

KAFKA_BOOTSTRAP = "localhost:9094"
KAFKA_TOPIC = "pgserver.public.users"

POSTGRES_DEST = "dbname=destination_db user=postgres password=postgres host=localhost port=5433"

consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP,
    auto_offset_reset="earliest",
    group_id="postgres-destination-consumer",
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

print("Consumer Postgres destino iniciado...")
print(f"Aguardando mensagens do topico: {KAFKA_TOPIC}")

with psycopg.connect(POSTGRES_DEST) as conn:
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                name VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        conn.commit()
        print("Tabela 'users' verificada/criada no destino")

for msg in consumer:
    try:
        payload = msg.value
        
        op = payload.get('op')
        after = payload.get('after', {})
        before = payload.get('before', {})
        
        with psycopg.connect(POSTGRES_DEST) as conn:
            with conn.cursor() as cur:
                if op == 'c':
                    cur.execute(
                        """
                        INSERT INTO users (id, username, name, created_at)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            username = EXCLUDED.username,
                            name = EXCLUDED.name,
                            created_at = EXCLUDED.created_at
                        """,
                        (
                            after.get('id'),
                            after.get('username'),
                            after.get('name'),
                            after.get('created_at')
                        )
                    )
                    print(f"INSERT: id={after.get('id')}, username={after.get('username')}")
                    
                elif op == 'u':
                    cur.execute(
                        """
                        UPDATE users 
                        SET username = %s, name = %s, created_at = %s
                        WHERE id = %s
                        """,
                        (
                            after.get('username'),
                            after.get('name'),
                            after.get('created_at'),
                            after.get('id')
                        )
                    )
                    print(f"UPDATE: id={after.get('id')}, username={after.get('username')}")
                    
                elif op == 'd':
                    cur.execute(
                        "DELETE FROM users WHERE id = %s",
                        (before.get('id'),)
                    )
                    print(f"DELETE: id={before.get('id')}")
                    
                else:
                    print(f"Operacao desconhecida: {op}")
                
                conn.commit()
                
    except Exception as e:
        print(f"Erro ao processar mensagem: {e}")
        import traceback
        traceback.print_exc()
