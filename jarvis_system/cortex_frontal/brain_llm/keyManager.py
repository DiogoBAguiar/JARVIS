# jarvis_system/cortex_frontal/brain_llm/key_manager.py
import os
import random
import logging
from typing import Optional
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger("BRAIN_KEYS")

class KeyManager:
    """Gerenciador de Rotação de Chaves para evitar Rate Limit"""
    def __init__(self):
        self.keys = []
        self._load_keys()
        self.current_index = 0

    def _load_keys(self):
        # 1. Pega a chave principal
        main_key = os.getenv("GROQ_API_KEY")
        if main_key:
            self.keys.append(main_key)
        
        # 2. Pega as chaves numeradas (GROQ_API_KEY_1 até _20)
        for i in range(1, 20):
            k = os.getenv(f"GROQ_API_KEY_{i}")
            if k:
                self.keys.append(k)
        
        # Embaralha para distribuir a carga entre reinícios
        if self.keys:
            random.shuffle(self.keys)
            log.info(f"🔑 KeyManager: {len(self.keys)} chaves Groq carregadas no pool.")
        else:
            log.critical("❌ Nenhuma chave GROQ_API_KEY encontrada no .env!")

    def get_client(self) -> Optional[Groq]:
        if not self.keys: return None
        return Groq(api_key=self.keys[self.current_index])

    def rotate(self):
        """Avança para a próxima chave da lista circularmente"""
        if not self.keys: return
        anterior = self.current_index
        self.current_index = (self.current_index + 1) % len(self.keys)
        log.warning(f"🔄 Rotacionando API Key: ID {anterior} -> ID {self.current_index}")