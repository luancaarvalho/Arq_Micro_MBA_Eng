#!/usr/bin/env python3
"""
Consumer simplificado - Lê do Kafka e insere no PostgreSQL Sink
Versão que ignora campos problemáticos e foca nos dados essenciais
"""

import json
import psycopg2
from kafka import KafkaConsumer
from datetime import datetime

# Configurações
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
KAFKA_TOPIC = 'cdc-source-server.public.products'

DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'sink_db',
    'user': 'postgres',
    'password': 'postgrespassword'
}

def convert_timestamp(microseconds):
    """Converte MicroTimestamp para TIMESTAMP"""
    if microseconds is None:
        return None
    try:
        dt = datetime.fromtimestamp(microseconds / 1_000_000)
        return dt
    except:
        return None

def safe_float(value, default=None):
    """Tenta converter para float de forma segura"""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except:
            return default
    return default

def process_message(message):
    """Processa uma mensagem do Kafka e insere no PostgreSQL"""
    try:
        if message.value is None:
            return False
            
        # Parse da mensagem JSON
        if isinstance(message.value, bytes):
            data = json.loads(message.value.decode('utf-8'))
        else:
            data = json.loads(message.value)
            
        payload = data.get('payload', {})
        
        # Verificar se é uma mensagem válida
        if not payload or payload.get('id') is None:
            return False
        
        # Extrair campos
        product_id = payload.get('id')
        name = payload.get('name')
        description = payload.get('description')
        
        # Para price, vamos buscar do banco fonte se não conseguir converter
        price = safe_float(payload.get('price'))
        if price is None:
            # Tentar buscar do banco fonte
            try:
                source_conn = psycopg2.connect(
                    host='localhost', port=5433,
                    database='source_db', user='postgres', password='postgrespassword'
                )
                source_cursor = source_conn.cursor()
                source_cursor.execute("SELECT price FROM products WHERE id = %s", (product_id,))
                result = source_cursor.fetchone()
                if result:
                    price = float(result[0])
                source_cursor.close()
                source_conn.close()
            except:
                price = 0.0  # Valor padrão
        
        category = payload.get('category')
        stock = payload.get('stock', 0) or 0
        created_at = convert_timestamp(payload.get('created_at'))
        updated_at = convert_timestamp(payload.get('updated_at'))
        op = payload.get('__op', 'c')
        
        if op == 'd':
            print(f"🗑️  DELETE: Removendo produto ID={product_id}")
            cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
        else:
            cursor.execute("""
                INSERT INTO products (id, name, description, price, category, stock, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    price = EXCLUDED.price,
                    category = EXCLUDED.category,
                    stock = EXCLUDED.stock,
                    updated_at = EXCLUDED.updated_at
            """, (product_id, name, description, price, category, stock, created_at, updated_at))
            
            print(f"✅ {op.upper()}: Produto ID={product_id}, Nome={name}, Preço={price}")
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao processar mensagem: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("CONSUMER SIMPLIFICADO - Kafka → PostgreSQL Sink")
    print("=" * 60)
    print()
    
    # Conectar ao PostgreSQL
    print("🔌 Conectando ao PostgreSQL sink...")
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    print("✅ Conectado!")
    print()
    
    # Criar tabela se não existir
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            price NUMERIC(10,2) NOT NULL,
            category VARCHAR(100),
            stock INTEGER DEFAULT 0,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
    """)
    conn.commit()
    print("✅ Tabela 'products' verificada/criada")
    print()
    
    # Criar consumer
    print(f"📥 Conectando ao Kafka (tópico: {KAFKA_TOPIC})...")
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: m,
        auto_offset_reset='latest',  # Começar do final para evitar mensagens antigas problemáticas
        enable_auto_commit=True,
        group_id='simple-sink-consumer-v2'
    )
    print("✅ Consumer criado!")
    print()
    print("🔄 Aguardando novas mensagens... (Ctrl+C para parar)")
    print("💡 Dica: Execute 'python scripts/mutations.py' em outro terminal")
    print()
    
    try:
        message_count = 0
        for message in consumer:
            message_count += 1
            if process_message(message):
                print(f"   📊 Total processado: {message_count}")
            print()
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Parando consumer...")
    finally:
        consumer.close()
        cursor.close()
        conn.close()
        print("✅ Conexões fechadas")

