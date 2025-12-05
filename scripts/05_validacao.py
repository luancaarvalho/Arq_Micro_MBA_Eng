import psycopg
import boto3
try:
    from botocore.exceptions import ClientError
except ImportError:
    class ClientError(Exception):
        pass
import json

SOURCE_DB = "dbname=source_db user=postgres password=postgres host=localhost port=5434"
DEST_DB = "dbname=destination_db user=postgres password=postgres host=localhost port=5433"

MINIO_ENDPOINT = "http://localhost:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "admin123"
MINIO_BUCKET = "kafka-files"

def validar_postgres_source():
    print("\nValidando Postgres SOURCE...")
    try:
        with psycopg.connect(SOURCE_DB) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM users")
                count = cur.fetchone()[0]
                print(f"Total de registros: {count}")
                
                cur.execute("SELECT id, name, username, created_at FROM users ORDER BY id LIMIT 5")
                records = cur.fetchall()
                if records:
                    print("Primeiros 5 registros:")
                    for record in records:
                        print(f"ID: {record[0]}, Nome: {record[1]}, Username: {record[2]}")
                return count, records
    except Exception as e:
        print(f"Erro ao validar source: {e}")
        return None, None

def validar_postgres_destination():
    print("\nValidando Postgres DESTINATION...")
    try:
        with psycopg.connect(DEST_DB) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM users")
                count = cur.fetchone()[0]
                print(f"Total de registros: {count}")
                
                cur.execute("SELECT id, name, username, created_at FROM users ORDER BY id LIMIT 5")
                records = cur.fetchall()
                if records:
                    print("Primeiros 5 registros:")
                    for record in records:
                        print(f"ID: {record[0]}, Nome: {record[1]}, Username: {record[2]}")
                return count, records
    except Exception as e:
        print(f"Erro ao validar destination: {e}")
        return None, None

def validar_minio():
    print("\nValidando MinIO...")
    try:
        minio_client = boto3.client(
            "s3",
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=MINIO_ACCESS_KEY,
            aws_secret_access_key=MINIO_SECRET_KEY,
            region_name="us-east-1"
        )
        
        try:
            response = minio_client.list_objects_v2(Bucket=MINIO_BUCKET)
            objects = response.get('Contents', [])
            count = len(objects)
            print(f"Total de arquivos: {count}")
            
            if objects:
                print("Ultimos 5 arquivos:")
                for obj in sorted(objects, key=lambda x: x['LastModified'], reverse=True)[:5]:
                    print(f"{obj['Key']} ({obj['Size']} bytes)")
            
            return count
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                print(f"Bucket '{MINIO_BUCKET}' nao existe ainda")
                return 0
            raise
    except Exception as e:
        print(f"Erro ao validar MinIO: {e}")
        return None

def comparar_source_destination():
    print("\nComparando Source vs Destination...")
    try:
        with psycopg.connect(SOURCE_DB) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name, username FROM users ORDER BY id")
                source_records = {r[0]: (r[1], r[2]) for r in cur.fetchall()}
        
        with psycopg.connect(DEST_DB) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name, username FROM users ORDER BY id")
                dest_records = {r[0]: (r[1], r[2]) for r in cur.fetchall()}
        
        source_ids = set(source_records.keys())
        dest_ids = set(dest_records.keys())
        
        missing_in_dest = source_ids - dest_ids
        extra_in_dest = dest_ids - source_ids
        matching = source_ids & dest_ids
        
        print(f"Registros correspondentes: {len(matching)}")
        
        if missing_in_dest:
            print(f"Registros faltando no destino: {len(missing_in_dest)}")
            for id in list(missing_in_dest)[:5]:
                print(f"ID {id}: {source_records[id]}")
        
        if extra_in_dest:
            print(f"Registros extras no destino: {len(extra_in_dest)}")
        
        if not missing_in_dest and not extra_in_dest:
            print("Source e Destination estao sincronizados!")
        
    except Exception as e:
        print(f"Erro ao comparar: {e}")

if __name__ == '__main__':
    print("=" * 60)
    print("VALIDACAO DO PIPELINE CDC")
    print("=" * 60)
    
    source_count, source_records = validar_postgres_source()
    dest_count, dest_records = validar_postgres_destination()
    minio_count = validar_minio()
    
    comparar_source_destination()
    
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    print(f"Source: {source_count or 0} registros")
    print(f"Destination: {dest_count or 0} registros")
    print(f"MinIO: {minio_count or 0} arquivos")
    print("=" * 60)
