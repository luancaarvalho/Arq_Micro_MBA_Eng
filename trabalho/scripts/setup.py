import subprocess
import time
import json
import os
import sys
from minio import Minio
from minio.error import S3Error

GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
BLUE = "\033[34m"
NC = "\033[0m"


def run(cmd, silent=False):
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL)
        return out.decode().strip()
    except:
        if not silent:
            print(RED + f"Erro executando: {cmd}" + NC)
        return ""


def wait_for_service(check_cmd, name, timeout=60):
    print(f"{YELLOW}  Aguardando {name}...{NC}")
    start = time.time()

    while time.time() - start < timeout:
        if run(check_cmd, silent=True):
            print(f"   {GREEN}{name} pronto!{NC}")
            return True
        time.sleep(2)

    print(f"{RED}Timeout aguardando {name}{NC}")
    return False


print("============================================================")
print(" SETUP CDC PIPELINE - PYTHON")
print("============================================================\n")

WORK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONNECTORS_DIR = os.path.join(WORK_DIR, "connectors")

# ------------------------------
# 1) AGUARDAR POSTGRES SOURCE
# ------------------------------
wait_for_service(
    "docker exec postgres-source pg_isready -U postgres -d source_db",
    "PostgreSQL fonte",
)

# ------------------------------
# 2) AGUARDAR POSTGRES SINK
# ------------------------------
wait_for_service(
    "docker exec postgres-sink pg_isready -U postgres -d sink_db", "PostgreSQL destino"
)

# ------------------------------
# 3) AGUARDAR KAFKA CONNECT
# ------------------------------
wait_for_service("curl -s http://localhost:8083", "Kafka Connect")

# ------------------------------
# 4) CRIAR TABELA PRODUCTS
# ------------------------------
print(f"\n{YELLOW}  Criando tabela 'products' no PostgreSQL fonte...{NC}")

SQL = """
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    category VARCHAR(100),
    stock INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_products_updated_at ON products;

CREATE TRIGGER update_products_updated_at
BEFORE UPDATE ON products
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
"""

with open("create_table.sql", "w") as f:
    f.write(SQL)

run("docker cp create_table.sql postgres-source:/create_table.sql")
run("docker exec postgres-source psql -U postgres -d source_db -f /create_table.sql")
os.remove("create_table.sql")

print(f"   {GREEN}Tabela criada!{NC}")

# ------------------------------
# 5) CONFIGURAR MINIO via Python SDK
# ------------------------------
print(f"\n{YELLOW}  Configurando MinIO...{NC}")

try:
    minio_client = Minio(
        "localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False,
    )

    # Testa comunicação
    minio_client.list_buckets()
    print(f"   {GREEN}MinIO acessível!{NC}")

    bucket = "cdc-data"
    if not minio_client.bucket_exists(bucket):
        minio_client.make_bucket(bucket)
        print(f"   {GREEN}Bucket '{bucket}' criado!{NC}")
    else:
        print(f"   {BLUE}Bucket '{bucket}' já existe.{NC}")

except Exception as e:
    print(f"{YELLOW}MinIO não está acessível. Ignorando parte do S3.{NC}")
    print("   Detalhes:", e)


# ------------------------------
# 6) REGISTRAR CONECTORES
# ------------------------------
def register_connector(path):
    name = os.path.basename(path).replace(".json", "")
    print(f"{YELLOW}  Registrando conector: {name}{NC}")

    if not os.path.exists(path):
        print(f"{RED}Arquivo não encontrado: {path}{NC}")
        return

    # Deleta se já existir
    run(f"curl -s -X DELETE http://localhost:8083/connectors/{name}")

    cmd = f'curl -s -X POST http://localhost:8083/connectors -H "Content-Type: application/json" --data @{path}'
    out = run(cmd)

    if '"name"' in out:
        print(f"{GREEN}  Conector {name} registrado!{NC}")
    else:
        print(f"{RED}  ERRO registrando {name}{NC}")
        print(out)


print(f"\n{YELLOW} Registrando conectores...{NC}")

register_connector(os.path.join(CONNECTORS_DIR, "debezium-source.json"))
time.sleep(5)
register_connector(os.path.join(CONNECTORS_DIR, "jdbc-sink-postgres.json"))

# ------------------------------
# 7) STATUS DOS CONECTORES
# ------------------------------
print(f"\n{YELLOW}  Verificando status dos conectores...{NC}")

for name in ["debezium-postgres-source", "jdbc-sink-postgres"]:
    raw = run(f"curl -s http://localhost:8083/connectors/{name}/status")
    try:
        state = json.loads(raw)["connector"]["state"]
    except:
        state = "UNKNOWN"
    print(f"   {name}: {state}")

print(f"\n{GREEN}Setup concluído com sucesso!{NC}")
print(
    """
Próximos passos:
1. python scripts/initial_load.py
2. python scripts/mutations.py
3. python scripts/validate.py
"""
)

# ------------------------------
# 8) INICIAR CONSUMIDOR KAFKA → MINIO AUTOMATICAMENTE
# ------------------------------
print(f"\n{YELLOW}Iniciando consumidor Kafka → MinIO...{NC}")

KAFKA_TO_MINIO = os.path.join(WORK_DIR, "scripts", "kafka_to_minio.py")
LOGFILE = os.path.join(WORK_DIR, ".logs", "kafka_to_minio.log")

os.makedirs(os.path.join(WORK_DIR, ".logs"), exist_ok=True)

# Verifica se já está rodando
check_running = run('wmic process where "CommandLine like \'%kafka_to_minio.py%\'" get ProcessId', silent=True)

if check_running.strip():
    print(f"   {YELLOW}Consumidor já está em execução. Ignorando.{NC}")
else:
    print("   Iniciando consumidor em background...")
    run(f'start "" python "{KAFKA_TO_MINIO}" > "{LOGFILE}" 2>&1')
    print(f"   {GREEN}Consumidor iniciado! Log: {LOGFILE}{NC}")