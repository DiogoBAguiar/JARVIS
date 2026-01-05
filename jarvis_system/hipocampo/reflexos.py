import json
import os
from typing import Dict
from jarvis_system.cortex_frontal.observability import JarvisLogger

log = JarvisLogger("HIPOCAMPO_REFLEXOS")

class ReflexMemory:
    """
    Gerencia memória associativa rápida (Key-Value) para correções fonéticas e atalhos.
    Representa a plasticidade do sistema auditivo.
    """
    def __init__(self):
        # Caminho para o arquivo JSON de aprendizado
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.file_path = os.path.join(base_dir, "data", "learned_aliases.json")
        self.aliases: Dict[str, str] = {}
        self._load()

    def _load(self):
        """Carrega aprendizados anteriores do disco."""
        if not os.path.exists(os.path.dirname(self.file_path)):
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.aliases = json.load(f)
                log.info(f"🧠 Reflexos carregados: {len(self.aliases)} correções aprendidas.")
            except Exception as e:
                log.error(f"Erro ao carregar reflexos: {e}")
                self.aliases = {}
        else:
            self.aliases = {}

    def _save(self):
        """Persiste o aprendizado."""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.aliases, f, indent=4, ensure_ascii=False)
        except Exception as e:
            log.error(f"Erro ao salvar reflexo: {e}")

    def aprender(self, termo_incorreto: str, termo_correto: str):
        """
        Ensina ao sistema que X significa Y.
        Ex: aprender("zap", "whatsapp")
        """
        key = termo_incorreto.lower().strip()
        val = termo_correto.lower().strip()
        
        # Evita loops ou redundância
        if key == val: return
        
        self.aliases[key] = val
        self._save()
        log.info(f"🎓 APRENDIDO: '{key}' agora será entendido como '{val}'.")

    def corrigir(self, texto: str) -> str:
        """
        Aplica as correções aprendidas em uma string.
        Complexidade: O(N) onde N é o número de palavras. Rápido.
        """
        if not self.aliases: return texto
        
        words = texto.split()
        corrected_words = []
        
        for w in words:
            # Verifica se a palavra exata existe no mapa
            # Futuramente pode ser fuzzy, mas O(1) é melhor para latência agora
            w_clean = self.aliases.get(w.lower(), w)
            corrected_words.append(w_clean)
            
        return " ".join(corrected_words)

# Singleton
reflexos = ReflexMemory()