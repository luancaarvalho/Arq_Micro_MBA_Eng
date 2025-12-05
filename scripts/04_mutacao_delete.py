import psycopg
import sys

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        user_id = int(sys.argv[1])
    else:
        print("Usando primeiro registro encontrado. Use: python 04_mutacao_delete.py <id>")
        with psycopg.connect("dbname=source_db user=postgres password=postgres host=localhost port=5434") as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name, username FROM users LIMIT 1")
                result = cur.fetchone()
                if not result:
                    print("Nenhum usuario encontrado. Execute primeiro a carga inicial.")
                    sys.exit(1)
                user_id = result[0]
    
    print(f"Removendo registro ID {user_id}...")
    
    try:
        with psycopg.connect("dbname=source_db user=postgres password=postgres host=localhost port=5434") as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name, username FROM users WHERE id = %s", (user_id,))
                record = cur.fetchone()
                
                if not record:
                    print(f"Erro: Registro com ID {user_id} nao encontrado!")
                    sys.exit(1)
                
                print(f"Registro a ser removido: {record[1]} ({record[2]})")
                
                cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
                
                if cur.rowcount == 0:
                    print(f"Nenhum registro foi removido!")
                    sys.exit(1)
                
                conn.commit()
                print(f"Registro removido com sucesso!")
                
    except Exception as e:
        print(f"Erro ao remover registro: {e}")
        raise
