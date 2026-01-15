import logging
from typing import Tuple

from .storage import ReflexosStorage
from .fuzzy_logic import aplicar_fuzzy
from .regex_compiler import compilar_padroes

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("HIPOCAMPO_REFLEXOS")

class HipocampoReflexos:
    def __init__(self):
        self.storage = ReflexosStorage()
        
        # Estado em Memória
        self.phonetic_map = {}
        self.ignored_phrases = []
        self.regex_patterns = []
        
        self.reload()

    def reload(self):
        """Recarrega tudo do disco."""
        self.phonetic_map = self.storage.carregar_manual()
        self.ignored_phrases = self.storage.carregar_intuicao()
        self.regex_patterns = compilar_padroes(self.phonetic_map)
        logger.info(f"Reflexos Carregados: {len(self.phonetic_map)} regras manuais, {len(self.ignored_phrases)} bloqueios aprendidos.")

    def processar_reflexo(self, texto: str) -> Tuple[str, bool]:
        if not texto or not isinstance(texto, str): return "", True
        
        texto_limpo = texto.strip().lower()

        # 1. BLOQUEIO (Subconsciente)
        if texto_limpo in self.ignored_phrases:
            logger.info(f"🚫 Bloqueado por Intuição: '{texto}'")
            return texto, True

        # 2. HEURÍSTICA (Tamanho)
        if len(texto_limpo) < 4 and "oi" not in texto_limpo:
             return texto, True

        # 3. CORREÇÃO
        texto_processado = texto
        original = texto
        
        try:
            # Regex (Exata)
            for pattern, correction in self.regex_patterns:
                texto_processado = pattern.sub(correction, texto_processado)
            
            # Fuzzy (Aproximada)
            texto_processado = aplicar_fuzzy(texto_processado, self.phonetic_map)

            if original != texto_processado:
                logger.info(f"⚡ Reflexo: '{original}' -> '{texto_processado}'")
                
        except Exception as e:
            logger.error(f"Erro processamento: {e}")
            return original, False

        return texto_processado, False

    def corrigir_texto(self, texto: str) -> str:
        t, _ = self.processar_reflexo(texto)
        return t

    def adicionar_correcao(self, errado: str, correto: str) -> bool:
        self.phonetic_map[errado.lower()] = correto
        if self.storage.salvar_manual(self.phonetic_map):
            self.reload()
            return True
        return False