#!/usr/bin/env python3
"""
Consumer que replica mensagens do Kafka para o PostgreSQL Sink
"""

import json
import psycopg2
from kafka import KafkaConsumer
import logging
from decimal import Decimal
import struct

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações
KAFKA_BROKER = 'localhost:9092'
KAFKA_TOPIC = 'cdc-source-server.public.products'
CONSUMER_GROUP = 'sink-replicator'

DB_SINK = {
    'host': 'localhost',
    'port': 5434,
    'database': 'sink_db',
    'user': 'postgres',
    'password': 'postgrespassword'
}

def decode_decimal(bytes_data):
    """Decodificar Decimal do Kafka Connect"""
    if not bytes_data or len(bytes_data) < 2:
        return None
    # Formato: scale(2 bytes) + value(N bytes big-endian)
    scale = struct.unpack('>H', bytes_data[:2])[0]
    value = int.from_bytes(bytes_data[2:], byteorder='big', signed=True)
    return Decimal(value) / (10 ** scale)

def process_message(msg_value, conn):
    """Processa mensagem do Kafka e replica para o sink"""
    try:
        payload = msg_value['payload']
        op = payload.get('__op', 'c')  # c=create, u=update, d=delete
        
        # Decodificar decimal se necessário
        price = payload.get('price')
        if isinstance(price, str) and len(price) > 0:
            try:
                # Tenta decodificar como base64
                import base64
                price_bytes = base64.b64decode(price)
                price = float(decode_decimal(price_bytes))
            except:
                try:
                    price = float(price)
                except:
                    price = None
        
        cursor = conn.cursor()
        
        if op == 'd':
            # DELETE
            cursor.execute(
                "DELETE FROM products WHERE id = %s",
                (payload['id'],)
            )
            logger.info(f"DELETE: id={payload['id']}")
            
        elif op in ('c', 'u'):
            # INSERT or UPDATE (UPSERT)
            cursor.execute("""
                INSERT INTO products (id, name, description, price, category, stock, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, to_timestamp(%s/1000000), to_timestamp(%s/1000000))
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    price = EXCLUDED.price,
                    category = EXCLUDED.category,
                    stock = EXCLUDED.stock,
                    updated_at = EXCLUDED.updated_at
            """, (
                payload['id'],
                payload.get('name'),
                payload.get('description'),
                price,
                payload.get('category'),
                payload.get('stock', 0),
                payload.get('created_at', 0),
                payload.get('updated_at', 0)
            ))
            op_str = "INSERT" if op == 'c' else "UPDATE"
            logger.info(f"{op_str}: id={payload['id']}, name={payload.get('name')}")
        
        conn.commit()
        cursor.close()
        return True
        
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")
        if conn:
            conn.rollback()
        return False

def main():
    """Inicia o consumer"""
    logger.info(f"Conectando ao Kafka: {KAFKA_BROKER}")
    logger.info(f"Tópico: {KAFKA_TOPIC}")
    logger.info(f"Consumer Group: {CONSUMER_GROUP}")
    
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        group_id=CONSUMER_GROUP,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        max_poll_records=100
    )
    
    logger.info("✅ Consumer iniciado")
    
    try:
        conn = psycopg2.connect(**DB_SINK)
        logger.info("✅ Conectado ao PostgreSQL Sink")
        
        message_count = 0
        for message in consumer:
            message_count += 1
            if process_message(message.value, conn):
                if message_count % 10 == 0:
                    logger.info(f"Processadas {message_count} mensagens")
            
    except KeyboardInterrupt:
        logger.info("Consumer interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro: {e}")
    finally:
        if conn:
            conn.close()
        consumer.close()
        logger.info(f"Consumer finalizado. Total de mensagens: {message_count}")

if __name__ == "__main__":
    main()
