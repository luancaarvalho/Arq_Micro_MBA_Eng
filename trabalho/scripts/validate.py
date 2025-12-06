import psycopg2
import json
import subprocess
from minio import Minio
from minio.error import S3Error

GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
BLUE = "\033[34m"
NC = "\033[0m"


def run(cmd):
    try:
        return subprocess.check_output(cmd, shell=True).decode().strip()
    except:
        return ""


# ------------------------------
# EXECUTAR QUERY DE CONTAGEM
# ------------------------------
def pg_count(container, db):
    try:
        # IMPORTANTE → usar aspas duplas para funcionar no Windows
        cmd = (
            f"docker exec {container} psql -U postgres -d {db} "
            f'-t -A -c "SELECT COUNT(*) FROM products;"'
        )
        out = run(cmd)
        return int(out.strip())
    except:
        return None


print("============================================================")
print("VALIDAÇÃO DO PIPELINE CDC")
print("============================================================\n")

# -----------------------------------------
# 1) PostgreSQL Sink
# -----------------------------------------
print("1) PostgreSQL Sink")

ready = "accepting connections" in run(
    "docker exec postgres-sink pg_isready -U postgres -d sink_db"
)
if ready:
    print(f"   {GREEN}postgres-sink ready{NC}")
else:
    print(f"   {RED}postgres-sink not ready{NC}")

sink_count = pg_count("postgres-sink", "sink_db")
print(f"   Total produtos no sink: {sink_count}\n")

# -----------------------------------------
# 2) Comparação Fonte vs Sink
# -----------------------------------------
print("2) Comparação Fonte vs Sink")

source_count = pg_count("postgres-source", "source_db")
print(f"   Fonte: {source_count} | Sink: {sink_count}")

if sink_count == source_count and sink_count is not None:
    print(f"   {GREEN}Contagens coincidem{NC}")
else:
    print(f"   {YELLOW}Contagens diferentes{NC}")

# -----------------------------------------
# 3) MinIO (via API)
# -----------------------------------------
print("\n3) MinIO")

try:
    client = Minio(
        "localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False,
    )

    objs = client.list_objects("cdc-data", recursive=True)
    count = sum(1 for _ in objs)

    print(f"   {GREEN}MinIO acessível!{NC}")
    print(f"   Total de arquivos CDC recebidos: {count}")

except Exception as e:
    print(f"   {RED}MinIO não acessível{NC}")
    print("   Erro:", str(e))

# -----------------------------------------
# 4) Conectores
# -----------------------------------------
print("\n4) Status dos conectores")


def connector_status(name):
    raw = run(f"curl -s http://localhost:8083/connectors/{name}/status")
    try:
        return json.loads(raw)["connector"]["state"]
    except:
        return "UNKNOWN"


for c in ["debezium-postgres-source", "jdbc-sink-postgres"]:
    print(f"   {c}: {connector_status(c)}")

# -----------------------------------------
# Resumo
# -----------------------------------------
print("\nResumo:")
if sink_count == source_count:
    print(f"   {GREEN}CDC funcionando corretamente{NC}")
else:
    print(f"   {RED}Diferença detectada entre origem e destino!{NC}")

print("\nDicas:")
print("  - docker logs kafka-connect")
print("  - docker logs postgres-source")
print("  - docker logs minio")
