import os
import sys
import chromadb

# Ajusta o path para garantir que achamos a pasta certa
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, "data", "jarvis_memory_db")

print(f"🔥 INICIANDO PROTOCOLO DE RESET EM: {db_path}")

try:
    client = chromadb.PersistentClient(path=db_path)
    
    # 1. Apaga a gaveta suja (se existir)
    try:
        print("🗑️  Apagando 'episodic_memory' (1731 itens sujos)...")
        client.delete_collection("episodic_memory")
        print("✅ Gaveta 'episodic_memory' destruída.")
    except ValueError:
        print("⚠️  Gaveta 'episodic_memory' não existia.")

    # 2. Reseta a gaveta nova (para garantir zero duplicatas)
    try:
        print("✨ Limpando 'jarvis_knowledge_base'...")
        client.delete_collection("jarvis_knowledge_base")
    except:
        pass
        
    # Recria ela zerada
    client.get_or_create_collection("jarvis_knowledge_base")
    print("✅ Gaveta 'jarvis_knowledge_base' recriada e pronta para uso.")

    print("\n🏁 CONCLUÍDO. O Cérebro está limpo e pronto para aprender corretamente.")

except Exception as e:
    print(f"Erro: {e}")