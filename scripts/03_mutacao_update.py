import psycopg
import sys

if __name__ == '__main__':
    if len(sys.argv) >= 4:
        user_id = int(sys.argv[1])
        new_name = sys.argv[2]
        new_username = sys.argv[3]
    else:
        print("Usando valores padrao. Use: python 03_mutacao_update.py <id> <novo_nome> <novo_username>")
        with psycopg.connect("dbname=source_db user=postgres password=postgres host=localhost port=5434") as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name, username FROM users LIMIT 1")
                result = cur.fetchone()
                if not result:
                    print("Nenhum usuario encontrado. Execute primeiro a carga inicial.")
                    sys.exit(1)
                user_id, old_name, old_username = result
                new_name = f"{old_name} (Atualizado)"
                new_username = f"{old_username}_updated"
    
    print(f"Atualizando registro ID {user_id}...")
    print(f"Novo nome: {new_name}")
    print(f"Novo username: {new_username}")
    
    try:
        with psycopg.connect("dbname=source_db user=postgres password=postgres host=localhost port=5434") as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name, username FROM users WHERE id = %s", (user_id,))
                old_record = cur.fetchone()
                
                if not old_record:
                    print(f"Erro: Registro com ID {user_id} nao encontrado!")
                    sys.exit(1)
                
                print(f"Registro anterior: {old_record[1]} ({old_record[2]})")
                
                cur.execute(
                    "UPDATE users SET name = %s, username = %s WHERE id = %s",
                    (new_name, new_username, user_id)
                )
                
                if cur.rowcount == 0:
                    print(f"Nenhum registro foi atualizado!")
                    sys.exit(1)
                
                conn.commit()
                print(f"Registro atualizado com sucesso!")
                
    except psycopg.IntegrityError as e:
        print(f"Erro: Usuario '{new_username}' ja existe!")
        sys.exit(1)
    except Exception as e:
        print(f"Erro ao atualizar registro: {e}")
        raise
