import psycopg


if __name__ == '__main__':
    
    with psycopg.connect("dbname=source_db user=postgres password=postgres host=localhost port=5432") as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (name, username) VALUES (%s, %s)",
                ("Marcos12345", "maurelio12345")
            )