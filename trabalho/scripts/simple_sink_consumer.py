#!/usr/bin/env python3
"""
Consumer simples que lê do Kafka e insere no PostgreSQL Sink
Alternativa ao JDBC Sink Connector que está com problemas de conversão de tipos
"""

import json
import psycopg2
from kafka import KafkaConsumer
from datetime import datetime
import base64
from decimal import Decimal

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
        # MicroTimestamp está em microssegundos desde epoch
        dt = datetime.fromtimestamp(microseconds / 1_000_000)
        return dt
    except:
        return None

def convert_decimal(value):
    """Converte Decimal serializado (string base64 ou bytes) para float"""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        # Pode ser string numérica ou base64 codificada
        try:
            # Tentar como número primeiro
            return float(value)
        except ValueError:
            # Tentar decodificar como base64 (formato do Kafka Connect Decimal)
            try:
                # Decodificar base64
                decoded_bytes = base64.b64decode(value, validate=True)
                # Formato Decimal do Kafka Connect: 
                # - Primeiro byte: scale (0-127)
                # - Resto: unscaled value como big-endian signed integer
                if len(decoded_bytes) > 0:
                    scale = decoded_bytes[0] & 0x7F  # Apenas 7 bits para scale
                    if len(decoded_bytes) > 1:
                        # Calcular tamanho necessário para o integer
                        unscaled_bytes = decoded_bytes[1:]
                        # Converter para integer signed big-endian
                        unscaled = int.from_bytes(unscaled_bytes, byteorder='big', signed=True)
                        result = float(Decimal(unscaled) / (10 ** scale))
                        # Validar se o resultado faz sentido (preço deve ser positivo e razoável)
                        if result > 0 and result < 1000000:  # Preços entre 0 e 1 milhão
                            return result
            except Exception:
                pass
            # Se todas as tentativas falharem, retornar None
            return None
    if isinstance(value, bytes):
        try:
            # Formato Decimal: scale (1 byte) + unscaled (big-endian)
            if len(value) > 0:
                scale = value[0] & 0x7F
                if len(value) > 1:
                    unscaled = int.from_bytes(value[1:], byteorder='big', signed=True)
                    result = float(Decimal(unscaled) / (10 ** scale))
                    if result > 0 and result < 1000000:
                        return result
        except:
            try:
                return float(value.decode('utf-8'))
            except:
                return None
    return None

def process_message(message):
    """Processa uma mensagem do Kafka e insere no PostgreSQL"""
    try:
        # Verificar se message.value existe
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
            # Pode ser uma mensagem de controle ou tombstone
            return False
        
        # Extrair campos
        product_id = payload.get('id')
        name = payload.get('name')
        description = payload.get('description')
        price = convert_decimal(payload.get('price'))  # Converter Decimal
        category = payload.get('category')
        stock = payload.get('stock', 0) or 0
        created_at = convert_timestamp(payload.get('created_at'))
        updated_at = convert_timestamp(payload.get('updated_at'))
        op = payload.get('__op', 'c')  # c=create, u=update, d=delete
        
        if op == 'd':
            # DELETE
            print(f"🗑️  DELETE: Removendo produto ID={product_id}")
            cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
        else:
            # INSERT ou UPDATE
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
            
            print(f"✅ {op.upper()}: Produto ID={product_id}, Nome={name}")
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao processar mensagem: {e}")
        conn.rollback()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("CONSUMER SIMPLES - Kafka → PostgreSQL Sink")
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
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='simple-sink-consumer'
    )
    print("✅ Consumer criado!")
    print()
    print("🔄 Aguardando mensagens... (Ctrl+C para parar)")
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

