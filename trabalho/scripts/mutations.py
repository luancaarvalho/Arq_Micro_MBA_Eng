import psycopg2
import time
import sys
from datetime import datetime

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'source_db',
    'user': 'postgres',
    'password': 'postgrespassword'
}

def print_separator():
    print("=" * 60)

def execute_mutation(description, query, params=None):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print(f"\n{description}")
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"{cursor.rowcount} linha(s) afetada(s)")
        else:
            print(f"  Nenhuma linha afetada")
        
        cursor.close()
        conn.close()
        
        time.sleep(2)
        
    except psycopg2.Error as e:
        print(f"Erro: {e}")
        return False
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return False
    
    return True

def test_insert():
    print_separator()
    print("TESTE 1: INSERT - Inserindo novo produto")
    print_separator()
    
    query = """
        INSERT INTO products (name, description, price, category, stock)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, name
    """
    
    params = (
        'Samsung Galaxy S24 Ultra',
        'Smartphone Android com 512GB, câmera de 200MP',
        6999.99,
        'Eletrônicos',
        12
    )
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"Produto inserido: ID={result[0]}, Nome={result[1]}")
        time.sleep(2)
        return True
    except Exception as e:
        print(f"Erro: {e}")
        return False

def test_update():
    print_separator()
    print("TESTE 2: UPDATE - Atualizando preço e estoque")
    print_separator()
    
    query = """
        UPDATE products 
        SET price = %s, stock = %s, updated_at = CURRENT_TIMESTAMP
        WHERE name = 'Notebook Dell XPS 15'
        RETURNING id, name, price, stock
    """
    
    params = (8499.99, 8)  
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        if result:
            print(f"Produto atualizado: ID={result[0]}, Nome={result[1]}")
            print(f"Novo preço: R$ {result[2]}, Novo estoque: {result[3]}")
        else:
            print("Produto não encontrado para atualização")
        time.sleep(2)
        return True
    except Exception as e:
        print(f" Erro: {e}")
        return False

def test_delete():
    print_separator()
    print("TESTE 3: DELETE - Removendo produto")
    print_separator()
    
    query = """
        DELETE FROM products 
        WHERE name = 'Teclado Mecânico Keychron'
        RETURNING id, name
    """
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        if result:
            print(f"Produto removido: ID={result[0]}, Nome={result[1]}")
        else:
            print("Produto não encontrado para remoção")
        time.sleep(2)
        return True
    except Exception as e:
        print(f"Erro: {e}")
        return False

def test_multiple_updates():
    print_separator()
    print("TESTE 4: MÚLTIPLAS ATUALIZAÇÕES")
    print_separator()
    
    updates = [
        ("iPhone 15 Pro", 7499.00, 20),
        ("Monitor LG UltraWide", 2299.99, 12),
        ("Mouse Logitech MX Master 3", 399.99, 18)
    ]
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        for name, new_price, new_stock in updates:
            cursor.execute("""
                UPDATE products 
                SET price = %s, stock = %s, updated_at = CURRENT_TIMESTAMP
                WHERE name = %s
                RETURNING id, name
            """, (new_price, new_stock, name))
            
            result = cursor.fetchone()
            if result:
                print(f"{result[1]}: Preço R$ {new_price}, Estoque {new_stock}")
            time.sleep(1)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        time.sleep(2)
        return True
    except Exception as e:
        print(f" Erro: {e}")
        return False

def main():
    print("=" * 60)
    print("MUTAÇÕES - Teste de INSERT/UPDATE/DELETE")
    print("=" * 60)
    print()
    print("Este script testa o pipeline CDC executando:")
    print("  1. INSERT - Inserção de novo produto")
    print("  2. UPDATE - Atualização de preço e estoque")
    print("  3. DELETE - Remoção de produto")
    print("  4. MÚLTIPLAS ATUALIZAÇÕES - Várias atualizações sequenciais")
    print()
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.close()
        print("Conexão com PostgreSQL fonte estabelecida")
    except Exception as e:
        print(f"Erro ao conectar: {e}")
        sys.exit(1)
    
    print()
    input("Pressione ENTER para iniciar os testes...")
    print()
    
    results = []
    results.append(("INSERT", test_insert()))
    results.append(("UPDATE", test_update()))
    results.append(("DELETE", test_delete()))
    results.append(("MÚLTIPLAS ATUALIZAÇÕES", test_multiple_updates()))
    
    print()
    print_separator()
    print("📊 RESUMO DOS TESTES")
    print_separator()
    
    for test_name, success in results:
        status = " PASSOU" if success else " FALHOU"
        print(f"  {test_name}: {status}")
    
    print()
    print(" Aguarde alguns segundos e execute 'python scripts/validate.py' para validar os dados nos destinos")

if __name__ == "__main__":
    main()

