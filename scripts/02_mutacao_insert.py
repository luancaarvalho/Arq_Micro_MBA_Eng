import psycopg
import sys

if __name__ == '__main__':
    if len(sys.argv) >= 3:
        name = sys.argv[1]
        username = sys.argv[2]
    else:
        name = "Novo Usuário"
        username = f"usuario_{int(__import__('time').time())}"
    
    print(f"Inserindo novo registro: {name} ({username})")
    
    try:
        with psycopg.connect("dbname=source_db user=postgres password=postgres host=localhost port=5434") as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (name, username) VALUES (%s, %s)",
                    (name, username)
                )
                conn.commit()
                print(f"Registro inserido com sucesso!")
                print(f"ID: {cur.lastrowid if hasattr(cur, 'lastrowid') else 'N/A'}")
                
    except psycopg.IntegrityError as e:
        print(f"Erro: Usuario '{username}' ja existe!")
        sys.exit(1)
    except Exception as e:
        print(f"Erro ao inserir registro: {e}")
        raise
