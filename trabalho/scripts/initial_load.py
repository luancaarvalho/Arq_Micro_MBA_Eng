#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de carga inicial - Insere dados iniciais na tabela products
"""

import psycopg2
import sys
from datetime import datetime

# Configuração do banco fonte
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'source_db',
    'user': 'postgres',
    'password': 'postgrespassword'
}

# Dados iniciais para inserção
INITIAL_PRODUCTS = [
    {
        'name': 'Notebook Dell XPS 15',
        'description': 'Notebook premium com Intel i7, 16GB RAM, SSD 512GB',
        'price': 8999.99,
        'category': 'Eletrônicos',
        'stock': 10
    },
    {
        'name': 'iPhone 15 Pro',
        'description': 'Smartphone Apple com 256GB de armazenamento',
        'price': 7999.00,
        'category': 'Eletrônicos',
        'stock': 25
    },
    {
        'name': 'Monitor LG UltraWide',
        'description': 'Monitor 34 polegadas, 4K, Curvo',
        'price': 2499.99,
        'category': 'Periféricos',
        'stock': 15
    },
    {
        'name': 'Teclado Mecânico Keychron',
        'description': 'Teclado mecânico sem fio, switches Gateron Brown',
        'price': 599.99,
        'category': 'Periféricos',
        'stock': 30
    },
    {
        'name': 'Mouse Logitech MX Master 3',
        'description': 'Mouse sem fio ergonômico para produtividade',
        'price': 449.99,
        'category': 'Periféricos',
        'stock': 20
    }
]

def insert_initial_data():
    """Insere dados iniciais na tabela products"""
    try:
        print("🔌 Conectando ao PostgreSQL fonte...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print(f"📦 Inserindo {len(INITIAL_PRODUCTS)} produtos iniciais...")
        
        for product in INITIAL_PRODUCTS:
            cursor.execute("""
                INSERT INTO products (name, description, price, category, stock)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                product['name'],
                product['description'],
                product['price'],
                product['category'],
                product['stock']
            ))
            
            product_id = cursor.fetchone()[0]
            print(f"   ✅ Produto inserido: ID={product_id}, Nome={product['name']}")
        
        conn.commit()
        print(f"\n✅ Carga inicial concluída! {len(INITIAL_PRODUCTS)} produtos inseridos.")
        
        # Verificar total de produtos
        cursor.execute("SELECT COUNT(*) FROM products")
        total = cursor.fetchone()[0]
        print(f"📊 Total de produtos na tabela: {total}")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ Erro ao inserir dados: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("CARGA INICIAL - Pipeline CDC")
    print("=" * 60)
    print()
    insert_initial_data()
    print()
    print("💡 Próximo passo: Execute 'python scripts/mutations.py' para testar INSERT/UPDATE/DELETE")

