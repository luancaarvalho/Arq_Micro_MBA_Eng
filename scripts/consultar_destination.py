import psycopg

DEST_DB = "dbname=destination_db user=postgres password=postgres host=localhost port=5433"

print("Consultando dados no Postgres Destination...")
print("=" * 60)

try:
    with psycopg.connect(DEST_DB) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users")
            count = cur.fetchone()[0]
            print(f"Total de registros: {count}\n")
            
            if count > 0:
                cur.execute("SELECT id, name, username, created_at FROM users ORDER BY id")
                records = cur.fetchall()
                print("Registros na tabela users:")
                print("-" * 60)
                print(f"{'ID':<5} {'Nome':<30} {'Username':<20} {'Created At'}")
                print("-" * 60)
                for record in records:
                    print(f"{record[0]:<5} {record[1]:<30} {record[2]:<20} {record[3]}")
            else:
                print("Nenhum registro encontrado.")
                
except Exception as e:
    print(f"Erro ao consultar banco: {e}")

