# jarvis_system/cortex_frontal/orchestrator/attention.py
import time
from difflib import SequenceMatcher
from .configOrchestrator import WAKE_WORDS, ATTENTION_WINDOW

class AttentionSystem:
    def __init__(self):
        self.last_activation = 0.0

    def check(self, text: str) -> tuple[bool, str]:
        """
        Verifica se o texto é para o Jarvis.
        Retorna (is_active, payload_limpo).
        """
        now = time.time()
        time_diff = now - self.last_activation
        
        # 1. Janela de Atenção Ativa (Contexto contínuo)
        if time_diff < ATTENTION_WINDOW:
            self.last_activation = now
            # Tenta remover o nome do Jarvis se o usuário disser "Jarvis, faz x" mesmo já estando ativo
            payload = self._strip_wake_word(text)
            return True, payload

        # 2. Precisa da Wake Word
        is_wake, payload = self._has_wake_word(text)
        if is_wake:
            self.last_activation = now
            return True, payload
            
        return False, ""

    def _strip_wake_word(self, text: str) -> str:
        words = text.split()
        for i, w in enumerate(words):
            if any(self._is_similar(w, wake) for wake in WAKE_WORDS):
                return " ".join(words[:i] + words[i+1:]).strip()
        return text

    def _has_wake_word(self, text: str) -> tuple[bool, str]:
        if not text: return False, ""
        
        # Verifica início da frase
        first_word = text.split()[0]
        for wake in WAKE_WORDS:
            if self._is_similar(first_word, wake):
                return True, text[len(first_word):].strip()
            
            # Verifica no meio da frase (ex: "Oi Jarvis")
            if f" {wake} " in f" {text} ":
                parts = text.split(wake, 1)
                # Só aceita se o que vem antes for curto (saudação)
                if len(parts[0]) < 15: 
                    return True, parts[1].strip()
                    
        return False, ""

    def _is_similar(self, a, b, threshold=0.8):
        return SequenceMatcher(None, a.lower(), b.lower()).ratio() >= threshold