import requests
import os
import re
from .configSpeak import FISH_AUDIO_API_URL, FISH_API_KEY, FISH_MODEL_ID, FISH_TAGS

class FishSynthesizer:
    def __init__(self, logger):
        self.log = logger

    def synthesize(self, text, metadata, output_path):
        if not FISH_API_KEY:
            self.log.error("API Key Fish Audio não configurada.")
            return False

        # --- LÓGICA DE INJEÇÃO DE TAGS (REFINADA) ---
        # 1. Pegamos os dados do metadata
        cat = metadata.get('category', 'GENERICO')
        sub = metadata.get('sub_context', 'passive')
        emotion = metadata.get('emotion', 'neutral')

        # 2. Prioridade de Tag: 
        #    A. Se houver emoção manual (ex: 'serious'), procuramos no mapa.
        #    B. Se não, tentamos Categoria.
        #    C. Por fim, tentamos Sub-contexto.
        
        tag = ""
        # Se a emoção for algo como 'serious', 'happy', etc.
        if emotion != "neutral":
            # Tenta pegar no configSpeak, se não existir, cria a tag no formato (emotion)
            tag = FISH_TAGS.get(emotion, f"({emotion})")
        else:
            tag = FISH_TAGS.get(cat, FISH_TAGS.get(sub, ""))

        # 3. Limpeza Final: Garante que o 'text' que veio não contém tags repetidas
        # Isso evita o erro de: (serious) (serious) texto
        clean_text = re.sub(r'\(.*?\)', '', text).strip()
        
        # Montagem do Payload Final
        text_payload = f"{tag} {clean_text}".strip()
        self.log.info(f"🎭 Payload Enviado: '{text_payload}'")

        # --- ENVIO PARA API ---
        headers = {
            "Authorization": f"Bearer {FISH_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "text": text_payload,
            "format": "mp3",
            "latency": "balanced",
            "normalize": True,
            "reference_id": FISH_MODEL_ID
        }

        try:
            response = requests.post(FISH_AUDIO_API_URL, json=payload, headers=headers, timeout=15)
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                return True
            else:
                self.log.error(f"Erro API Fish: {response.text}")
                return False
        except Exception as e:
            self.log.error(f"Erro Conexão API: {e}")
            return False