import json
import os
import re
import sys

# Define caminhos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # jarvis_system
JSON_PATH = os.path.join(BASE_DIR, "data", "voices", "voice_index.json")

def normalizar_chave_oficial(texto: str) -> str:
    """
    CÓPIA EXATA da lógica do speak.py v2.5
    """
    if not texto: return ""
    # 1. Remove tags de emoção ex: (happy)
    texto = re.sub(r'\([^)]*\)', '', texto) 
    texto = texto.lower()
    
    # 2. Transliteração manual de acentos
    trans = str.maketrans("áàãâéêíóõôúç", "aaaaeeiooouc")
    texto = texto.translate(trans)
    
    # 3. Remove tudo que não for letra ou número
    return re.sub(r'[^a-z0-9]', '', texto)

def reparar_indices():
    if not os.path.exists(JSON_PATH):
        print(f"❌ Arquivo não encontrado: {JSON_PATH}")
        return

    print(f"🔧 Iniciando reparo em: {JSON_PATH}")
    
    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            dados = json.load(f)
    except Exception as e:
        print(f"❌ Erro ao ler JSON: {e}")
        return

    corrigidos = 0
    total = len(dados)
    novos_dados = {}

    for key_antiga, metadata in dados.items():
        texto_real = metadata.get("text", "")
        
        # Recalcula o hash oficial
        novo_hash = normalizar_chave_oficial(texto_real)
        
        # Atualiza o campo interno
        hash_antigo_interno = metadata.get("key_hash", "")
        metadata["key_hash"] = novo_hash
        
        # Salva no novo dicionário com a CHAVE do objeto corrigida
        novos_dados[novo_hash] = metadata
        
        if novo_hash != key_antiga or novo_hash != hash_antigo_interno:
            corrigidos += 1
            print(f"   🔄 Corrigido: {metadata['id']}")
            print(f"      Antigo: {key_antiga}")
            print(f"      Novo:   {novo_hash}")

    # Salva o arquivo corrigido
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(novos_dados, f, indent=4, ensure_ascii=False)

    print("-" * 30)
    print(f"✅ Sucesso! {corrigidos}/{total} entradas foram padronizadas.")
    print("🚀 Reinicie o J.A.R.V.I.S. agora.")

if __name__ == "__main__":
    reparar_indices()