import os
import sys
import time
from collections import Counter

# Adiciona raiz ao path para garantir imports corretos
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(root_dir)

try:
    from jarvis_system.hipocampo.memoria import memoria
except ImportError as e:
    print(f"❌ Erro de Importação: {e}")
    sys.exit(1)

def diagnostico_conexao():
    print("\n🔍 --- DIAGNÓSTICO DE CONEXÃO ---")
    print(f"📂 Raiz do Projeto: {root_dir}")
    print(f"📂 Caminho do Banco (Configurado): {memoria.db_path}")
    
    # Verifica se a pasta existe fisicamente
    if os.path.exists(memoria.db_path):
        print("✅ A pasta do banco de dados EXISTE fisicamente.")
        arquivos = os.listdir(memoria.db_path)
        print(f"   Conteúdo: {arquivos}")
        if "chroma.sqlite3" in arquivos:
            print("   ✅ Arquivo 'chroma.sqlite3' encontrado.")
        else:
            print("   ❌ ARQUIVO 'chroma.sqlite3' NÃO ENCONTRADO (Banco corrompido?).")
    else:
        print("❌ A pasta do banco de dados NÃO EXISTE.")

    # Tenta reconexão forçada
    if memoria.collection is None:
        print("\n⚠️ Conexão inicial nula. Tentando conectar manualmente agora...")
        memoria._conectar()
        
    if memoria.collection:
        qtd = memoria.collection.count()
        print(f"✅ CONEXÃO ESTABELECIDA! Itens na memória: {qtd}")
        return True
    else:
        print("❌ FALHA FINAL: Não foi possível conectar ao ChromaDB.")
        return False

def listar_estatisticas():
    print("\n📊 Carregando estatísticas...")
    try:
        # Pega todos os metadados
        dados = memoria.collection.get(include=['metadatas'])
        metadatas = dados.get('metadatas', [])
        
        if not metadatas:
            print("📭 A memória está vazia (0 itens).")
            return

        # Conta as tags
        contador = Counter()
        for meta in metadatas:
            tag = meta.get('tags', 'sem_tag')
            contador[tag] += 1

        print(f"\n{'TAG':<40} | {'QTD'}")
        print("-" * 50)
        for tag, count in contador.most_common():
            print(f"{tag:<40} | {count}")

    except Exception as e:
        print(f"Erro ao ler banco: {e}")

def espiar_tag():
    tag = input("\nQual tag você quer espiar? ").strip()
    res = memoria.collection.get(where={"tags": tag}, limit=5)
    docs = res.get('documents', [])
    
    if docs:
        print(f"\n--- Amostra de '{tag}' ---")
        for d in docs:
            print(f"🔹 {d}")
    else:
        print("Nada encontrado.")

def menu():
    if not diagnostico_conexao():
        return

    while True:
        print("\n" + "="*40)
        print("🧠 GERENCIADOR DE MEMÓRIA V2")
        print("="*40)
        print("1. Listar Estatísticas (O que eu sei?)")
        print("2. Espiar uma Tag")
        print("3. Sair")
        
        opt = input("\nOpção: ")
        
        if opt == "1": listar_estatisticas()
        elif opt == "2": espiar_tag()
        elif opt == "3": break

if __name__ == "__main__":
    menu()