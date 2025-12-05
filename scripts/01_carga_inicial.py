import psycopg
import time

USUARIOS_INICIAIS = [
    ("João Silva", "joao.silva"),
    ("Maria Santos", "maria.santos"),
    ("Pedro Oliveira", "pedro.oliveira"),
    ("Ana Costa", "ana.costa"),
    ("Carlos Pereira", "carlos.pereira"),
    ("Julia Ferreira", "julia.ferreira"),
    ("Roberto Alves", "roberto.alves"),
    ("Fernanda Lima", "fernanda.lima"),
    ("Lucas Souza", "lucas.souza"),
    ("Patricia Rocha", "patricia.rocha"),
]

if __name__ == '__main__':
    print("Iniciando carga inicial de dados...")
    print(f"Total de registros a inserir: {len(USUARIOS_INICIAIS)}")
    
    try:
        with psycopg.connect("dbname=source_db user=postgres password=postgres host=localhost port=5434") as conn:
            with conn.cursor() as cur:
                inseridos = 0
                for name, username in USUARIOS_INICIAIS:
                    try:
                        cur.execute(
                            "INSERT INTO users (name, username) VALUES (%s, %s)",
                            (name, username)
                        )
                        inseridos += 1
                        print(f"Inserido: {name} ({username})")
                        time.sleep(0.5)
                    except psycopg.IntegrityError as e:
                        print(f"Usuario {username} ja existe, pulando...")
                
                conn.commit()
                print(f"\nCarga inicial concluida! {inseridos} registros inseridos.")
                
    except Exception as e:
        print(f"Erro durante carga inicial: {e}")
        raise
