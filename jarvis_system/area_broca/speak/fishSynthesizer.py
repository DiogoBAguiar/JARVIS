# jarvis_system/area_broca/speak/synthesizer.py
import requests
import os
from .configSpeak import FISH_AUDIO_API_URL, FISH_API_KEY, FISH_MODEL_ID, FISH_TAGS

class FishSynthesizer:
    def __init__(self, logger):
        self.log = logger

    def synthesize(self, text, metadata, output_path):
        if not FISH_API_KEY:
            self.log.error("API Key Fish Audio não configurada.")
            return False

        # Injeção de Tags
        cat = metadata['category']
        sub = metadata['sub_context']
        tag = FISH_TAGS.get(cat, FISH_TAGS.get(sub, ""))
        
        text_payload = f"{tag} {text}".strip()
        self.log.info(f"🎭 Payload: '{text_payload}'")

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