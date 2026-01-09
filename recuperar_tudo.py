import os
import sys
import re
import chromadb
from chromadb.config import Settings

# Garante raiz do projeto
sys.path.append(os.getcwd())
from jarvis_system.hipocampo.memoria import memoria

print("🛠️ Iniciando Operação de Resgate de Dados...")

# 1. APONTAR PARA O BANCO CORRETO (O de 3MB)
CAMINHO_BANCO_GRANDE = r"D:\projetos\J.A.R.V.I.S\data\jarvis_memory_db"

client_resgate = chromadb.PersistentClient(
    path=CAMINHO_BANCO_GRANDE,
    settings=Settings(allow_reset=True, anonymized_telemetry=False)
)

# 2. LISTAR TODAS AS COLEÇÕES DENTRO DELE
colecoes = client_resgate.list_collections()
print(f"📦 Coleções encontradas no banco de 3MB: {[c.name for c in colecoes]}")

PADRAO = re.compile(r"música ['\"](.+?)['\"] de ['\"](.+?)['\"]", re.IGNORECASE)

sucessos = 0

for col_info in colecoes:
    print(f"🔍 Vasculhando coleção: {col_info.name}...")
    col = client_resgate.get_collection(name=col_info.name)
    dados = col.get()
    
    docs = dados.get('documents', [])
    print(f"   - Encontrados {len(docs)} documentos.")

    for doc in docs:
        # Tenta extrair musica e artista do texto bruto
        match = PADRAO.search(doc)
        if match:
            musica, artista = match.group(1).strip(), match.group(2).strip()
            
            # SALVA NO NOVO FORMATO (Usando sua classe memoria oficial)
            memoria.memorizar_musica(musica, artista, tags="spotify_likes")
            sucessos += 1
            print(f"\r✅ Resgatado: {musica[:20]}...", end="")

print(f"\n\n🏆 Operação finalizada! {sucessos} músicas foram migradas para o novo formato.")
print(f"📡 Status atual da nova memória: {memoria.status()}")