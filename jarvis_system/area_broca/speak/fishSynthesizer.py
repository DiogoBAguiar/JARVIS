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

        # Verifica se o texto já começa com uma tag gerada nativamente pelo LLM (ex: "(amused) ...")
        match = re.match(r'^\(.*?\)', text.strip())
        
        if match:
            # O LLM enviou uma emoção! Vamos preservá-la e mandar do jeito que veio.
            text_payload = text.strip()
        else:
            # O LLM não mandou emoção no texto. Vamos usar a sua lógica de fallback (metadata)
            cat = metadata.get('category', 'GENERICO')
            sub = metadata.get('sub_context', 'passive')
            emotion = metadata.get('emotion', 'neutral')

            if emotion != "neutral":
                tag = FISH_TAGS.get(emotion, f"({emotion})")
            else:
                tag = FISH_TAGS.get(cat, FISH_TAGS.get(sub, ""))

            # Remove lixo para não duplicar, caso haja erro
            clean_text = re.sub(r'\(.*?\)', '', text).strip()
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