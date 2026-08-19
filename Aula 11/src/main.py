from pathlib import Path
import sqlite3

DATABASE_PATH = Path(__file__).parent.parent / "data" / "pipeline.db"
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

# ─── 2.1 Conexao, Cursor e Commit
def get_version():
  # 'with' faz commit automatico em sucesso e rollback em excecao
  with sqlite3.connect(DATABASE_PATH) as conn:
    cursor = conn.cursor()
    query = "SELECT sqlite_version()"
    
    cursor.execute(query)
    result = cursor.fetchone()
    
    return result
  
# ─── 2.2 CREATE TABLE — Definindo a Estrutura 
def create_table():
  with sqlite3.connect(DATABASE_PATH) as conn:
    cursor = conn.cursor()
    query = """
      CREATE TABLE IF NOT EXISTS documentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        origem TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pendente',
        num_tokens INTEGER ,
        criado_em TEXT DEFAULT (datetime('now', 'localtime'))
      )
    """
    
    cursor.execute(query)
    conn.commit()
    
    print("Tabela criada com sucesso")

# ─── 2.3 INSERT — Criando Registros
def insert_documento():
  with sqlite3.connect(DATABASE_PATH) as conn:
    cursor = conn.cursor()
    
    # INSERT com parametro unico (sempre use ? — nunca f-string)
    query = """
      INSERT INTO documentos (nome, origem, num_tokens) 
      VALUES (?, ?, ?)
    """
    
    cursor.execute(query, ("documento0.pdf", "local", 50))
    
    conn.commit()
    
    print(f"Documento documento0.pdf inserido com sucesso")
    
    # INSERT em lote — executemany() e mais eficiente que um loop
    
    documentos = [
      ("documento1.pdf", "local", 100),
      ("documento2.pdf", "local", 200),
      ("documento3.pdf", "local", 300),
    ]
    
    cursor.executemany(query, documentos)
    conn.commit()
    
    for documento in documentos:
      print(f"Documento {documento[0]} inserido com sucesso")

# ─── 2.4 SELECT — Consultando Registros
def get_documentos():
  with sqlite3.connect(DATABASE_PATH) as conn:
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Todos os registros
    query = 'SELECT * FROM documentos ORDER BY criado_em DESC'
    cursor.execute(query)
    
    print('\nTodos os registros:')
    
    for row in cursor.fetchall():
        print(dict(row))

    # Filtrar por status
    query = 'SELECT id, nome, status FROM documentos WHERE status = ?'
    cursor.execute(query, ('pendente',))
    
    pendentes = cursor.fetchall()
    
    print(f'\n{len(pendentes)} documentos pendentes')

    # Agregar: contar por status
    query = 'SELECT status, COUNT(*) as total FROM documentos GROUP BY status'
    cursor.execute(query)
    
    print('\nContagem por status:')
    
    for row in cursor.fetchall():
        print(f'{row["status"]}: {row["total"]}')
    
    query = 'SELECT * FROM documentos WHERE id = ?'
    cursor.execute(query, (1,))
    
    # fetchone() para busca por ID
    doc = cursor.fetchone()
    
    print('\nBusca por id=1:', doc['nome'] if doc else 'Nao encontrado')

# ─── 2.5 UPDATE e DELETE 
def update_delete():
  with sqlite3.connect(DATABASE_PATH) as conn:
    cursor = conn.cursor()
    
    # UPDATE: marcar documento como processado
    query = 'UPDATE documentos SET status = ? WHERE id = ?'
    cursor.execute(query, ('processado', 1))
    conn.commit()
  
    # UPDATE condicional
    query = 'UPDATE documentos SET status = ? WHERE num_tokens > ?'
    cursor.execute(query, ('fila_longa', 100))
    conn.commit()

    # Verificar quantas linhas foram afetadas
    query = 'UPDATE documentos SET status = ? WHERE origem = ?'
    cursor.execute(query, ('revisao', 'email'))
    conn.commit()
    
    print(f'\n{cursor.rowcount} linha(s) atualizada(s) para origem=email')

    # DELETE por ID
    query = 'DELETE FROM documentos WHERE id = ?'
    cursor.execute(query, (3,))
    conn.commit()
    
    print('Delecoes executadas.')
