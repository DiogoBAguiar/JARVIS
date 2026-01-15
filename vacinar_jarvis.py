import os
import json
import logging

# Configuração
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("VACINA")

INTUICAO_FILE = "jarvis_system/data/intuicao.json"

# --- LISTA DE ALUCINAÇÕES CONHECIDAS DO WHISPER (PT-BR) ---
# O Whisper foi treinado com legendas do YouTube/TV.
# Quando ele ouve ruído estático (ventilador), ele "chuta" essas frases.
VACINA_ANTIVIRUS = [
    # Créditos de Legenda (Muito comum em silêncio)
    "legendas pela comunidade amara.org",
    "legendado por",
    "tradução por",
    "editado por",
    "amara.org",
    
    # Alucinações Curtas
    "sousa",
    "souza",
    "pois é",
    "ah é",
    "tá bom",
    "então",
    "né",
    "obrigado",
    "obrigada",
    "bom dia",
    "boa noite",
    "inscreva-se",
    "deixe seu like",
    "tchau",
    
    # Ruídos interpretados
    "música",
    "aplausos",
    "risos",
    "silêncio",
    
    # Frases sem sentido que aparecem com ventilador
    "o que é que é",
    "o que é que tem",
    "eu não sei",
    "acha", 
    "isso é uma coisa de troço" # O seu caso específico
]

def aplicar_vacina():
    logger.info("💉 Preparando vacina contra alucinações do Whisper...")
    
    # 1. Carrega memória existente ou cria nova
    if os.path.exists(INTUICAO_FILE):
        with open(INTUICAO_FILE, 'r', encoding='utf-8') as f:
            memoria = json.load(f)
    else:
        os.makedirs(os.path.dirname(INTUICAO_FILE), exist_ok=True)
        memoria = {"ruido_ignorado": []}

    lista_atual = set(memoria.get("ruido_ignorado", []))
    tamanho_antes = len(lista_atual)
    
    # 2. Injeta os vírus conhecidos na lista negra
    logger.info(f"🦠 Adicionando {len(VACINA_ANTIVIRUS)} padrões conhecidos de ruído...")
    lista_atual.update(VACINA_ANTIVIRUS)
    
    # 3. Salva
    memoria["ruido_ignorado"] = list(lista_atual)
    
    with open(INTUICAO_FILE, 'w', encoding='utf-8') as f:
        json.dump(memoria, f, indent=4, ensure_ascii=False)
        
    novos = len(lista_atual) - tamanho_antes
    logger.info(f"✅ Vacinação concluída! {novos} novos anticorpos adicionados.")
    logger.info("🛡️ O Jarvis agora ignorará essas frases automaticamente.")

if __name__ == "__main__":
    aplicar_vacina()