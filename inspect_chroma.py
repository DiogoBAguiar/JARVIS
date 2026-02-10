import sqlite3
import os

# Caminho para o ficheiro do banco de dados
DB_PATH = os.path.join("jarvis_system", "data", "jarvis_memory_db", "chroma.sqlite3")

def inspect_db():
    if not os.path.exists(DB_PATH):
        print(f"❌ Erro: Ficheiro não encontrado em: {DB_PATH}")
        return

    print(f"🔍 Inspecionando: {DB_PATH}\n")
    
    try:
        # Conecta ao banco de dados SQLite (modo leitura)
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        cursor = conn.cursor()

        # 1. Listar todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        print(f"📊 Tabelas encontradas: {len(tables)}")
        for table in tables:
            table_name = table[0]
            print(f"\n{'='*40}")
            print(f"Tabela: {table_name}")
            print(f"{'='*40}")

            # 2. Contar registos
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"Total de registos: {count}")
            except:
                print("Não foi possível contar registos.")

            # 3. Mostrar estrutura das colunas (Schema)
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            col_names = [col[1] for col in columns]
            print(f"Colunas: {col_names}\n")

            # 4. Mostrar amostra de dados (Top 5)
            print("--- Amostra de Dados (Top 5) ---")
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            rows = cursor.fetchall()
            
            if not rows:
                print("(Tabela vazia)")
            
            for row in rows:
                # Trunca campos muito longos para facilitar leitura
                formatted_row = []
                for item in row:
                    s_item = str(item)
                    if len(s_item) > 100:
                        formatted_row.append(s_item[:100] + "...")
                    else:
                        formatted_row.append(s_item)
                print(formatted_row)

        conn.close()

    except sqlite3.Error as e:
        print(f"❌ Erro ao ler o banco de dados: {e}")

if __name__ == "__main__":
    inspect_db()