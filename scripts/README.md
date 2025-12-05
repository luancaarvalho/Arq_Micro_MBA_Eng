# Scripts do Pipeline CDC

Este diretório contém todos os scripts necessários para executar e validar o pipeline CDC.

## Scripts Disponíveis

### 1. Carga Inicial
- **`01_carga_inicial.py`** - Insere múltiplos registros na tabela fonte para demonstrar carga inicial

### 2. Mutações
- **`02_mutacao_insert.py`** - Insere um novo registro (demonstra captura de INSERT)
- **`03_mutacao_update.py`** - Atualiza um registro existente (demonstra captura de UPDATE)
- **`04_mutacao_delete.py`** - Remove um registro (demonstra captura de DELETE)

### 3. Validação
- **`05_validacao.py`** - Valida se os dados foram replicados corretamente nos destinos

## Como Usar

1. Execute a carga inicial primeiro:
   ```bash
   python scripts/01_carga_inicial.py
   ```

2. Execute mutações para testar o CDC:
   ```bash
   python scripts/02_mutacao_insert.py "Nome Usuario" "username"
   python scripts/03_mutacao_update.py <id> "Novo Nome" "novo_username"
   python scripts/04_mutacao_delete.py <id>
   ```

3. Valide os resultados:
   ```bash
   python scripts/05_validacao.py
   ```

