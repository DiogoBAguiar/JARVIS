import os
import sys
import chromadb

# Configura caminho
current_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(current_dir, "data") # Ajuste se necessário, mas o script abaixo acha sozinho
db_path = os.path.join(os.getcwd(), "data", "jarvis_memory_db")

print(f"📂 Lendo banco em: {db_path}")

try:
    client = chromadb.PersistentClient(path=db_path)
    colecoes = client.list_collections()
    
    print(f"\nEncontrei {len(colecoes)} coleções (gavetas):")
    
    for col in colecoes:
        qtd = col.count()
        print(f"📦 Gaveta: '{col.name}' | Itens: {qtd}")
        
except Exception as e:
    print(f"Erro: {e}")