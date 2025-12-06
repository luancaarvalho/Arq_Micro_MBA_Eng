import subprocess
import time
import json
import os
import sys
import platform
from minio import Minio

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


def start_kafka_to_minio():
    print("\nIniciando consumidor Kafka → MinIO...")

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    script_path = os.path.join(base_dir, "scripts", "kafka_to_minio.py")
    log_dir = os.path.join(base_dir, ".logs")
    log_file = os.path.join(log_dir, "kafka_to_minio.log")

    os.makedirs(log_dir, exist_ok=True)

    system = platform.system()

    if system == "Windows":
        cmd = f'start "" python "{script_path}" > "{log_file}" 2>&1'
        try:
            subprocess.Popen(cmd, shell=True)
            print(f"   Consumidor iniciado (Windows). Log: {log_file}")
        except Exception as e:
            print(RED + f"Erro ao iniciar consumidor no Windows: {e}" + NC)

    else:  # macOS / Linux
        cmd = f'nohup python "{script_path}" > "{log_file}" 2>&1 &'
        try:
            subprocess.Popen(cmd, shell=True, executable="/bin/bash")
            print(f"   Consumidor iniciado (Linux/macOS). Log: {log_file}")
        except Exception as e:
            print(RED + f"Erro ao iniciar consumidor no Linux/macOS: {e}" + NC)


# ---------------------------------------
# INÍCIO DO SCRIPT
# ---------------------------------------

print("============================================================")
print(" SETUP CDC PIPELINE - PYTHON")
print("============================================================\n")

WORK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONNECTORS_DIR = os.path.join(WORK_DIR, "connectors")

wait_for_service(
    "docker exec postgres-source pg_isready -U postgres -d source_db",
    "PostgreSQL fonte",
)

wait_for_service(
    "docker exec postgres-sink pg_isready -U postgres -d sink_db",
    "PostgreSQL destino",
)

wait_for_service("curl -s http://localhost:8083", "Kafka Connect")

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

print(f"\n{YELLOW}  Configurando MinIO...{NC}")
minio_ready = False

client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False,
)

try:
    if not client.bucket_exists("cdc-data"):
        client.make_bucket("cdc-data")
        print(f"   {GREEN}Bucket 'cdc-data' criado!{NC}")
    else:
        print(f"   {GREEN}Bucket 'cdc-data' já existe.{NC}")

    minio_ready = True
except Exception as e:
    print(f"{RED}Erro acessando MinIO:{NC}", e)

def register_connector(path):
    name = os.path.basename(path).replace(".json", "")
    print(f"{YELLOW}  Registrando conector: {name}{NC}")

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
time.sleep(4)
register_connector(os.path.join(CONNECTORS_DIR, "jdbc-sink-postgres.json"))

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

start_kafka_to_minio()
