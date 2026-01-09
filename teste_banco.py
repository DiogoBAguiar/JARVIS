import os
import sys

# Força o Python a ver a raiz do projeto
sys.path.append(os.getcwd())

try:
    print("1. Tentando importar memoria...")
    from jarvis_system.hipocampo.memoria import memoria
    
    print(f"2. Caminho do banco configurado: {memoria.db_path}")
    
    print("3. Tentando forçar conexão...")
    sucesso = memoria._conectar()
    
    if sucesso:
        print(f"✅ SUCESSO! Coleção carrega. Itens: {memoria.collection.count()}")
    else:
        print("❌ FALHA na conexão (veja o log acima se houver).")
        print(f"Estado da coleção: {memoria.collection}")

except Exception as e:
    print(f"💥 ERRO FATAL: {e}")
    import traceback
    traceback.print_exc()