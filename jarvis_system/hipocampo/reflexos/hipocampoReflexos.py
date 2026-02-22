import logging
import threading
from typing import Tuple, Set, List, Pattern, Dict, Any

from .reflexosStorage import ReflexosStorage
from .fuzzy_logic import aplicar_fuzzy
from .regex_compiler import compilar_padroes

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("HIPOCAMPO_REFLEXOS")

class HipocampoReflexos:
    _instance = None
    _init_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """
        Garante que apenas UMA instância desta classe exista na memória.
        Padrão Singleton thread-safe.
        """
        if not cls._instance:
            with cls._init_lock:
                if not cls._instance:
                    cls._instance = super(HipocampoReflexos, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        # Impede que o __init__ seja chamado novamente se a instância já existir
        if self._initialized:
            return
            
        self.storage = ReflexosStorage()
        self._lock = threading.RLock()
        
        self.phonetic_map = {}
        self.ignored_phrases: Set[str] = set()
        self.regex_patterns = [] # [(Pattern, callback)]
        
        self.reload()
        self._initialized = True

    def reload(self):
        with self._lock:
            try:
                self.phonetic_map = self.storage.carregar_manual() or {}
                raw_ignored = self.storage.carregar_intuicao() or []
                self.ignored_phrases = set(f.strip().lower() for f in raw_ignored)
                self.regex_patterns = compilar_padroes(self.phonetic_map)
                logger.info(f"✅ Reflexos: {len(self.phonetic_map)} regras, {len(self.ignored_phrases)} bloqueios.")
            except Exception as e:
                logger.error(f"❌ Erro reload: {e}")

    def processar_reflexo(self, texto: str) -> Tuple[str, bool]:
        """
        Processa o texto aplicando correções e retorna (texto_limpo, deve_ignorar).
        Retorna STRING simples para compatibilidade com sistemas legados.
        """
        if not texto or not isinstance(texto, str): return "", True
        
        # Chama a análise completa e extrai apenas o texto final
        analise = self.analisar_comando(texto)
        return analise["texto"], analise.get("bloqueado", False)

    def analisar_comando(self, texto: str) -> Dict[str, Any]:
        """
        Nova API Rica: Retorna objeto de análise completo para o Orquestrador.
        
        Retorno:
        {
            "texto": str (Texto corrigido final),
            "termo_detectado": str (Sugestão do DB, se houver),
            "termo_original": str (O que foi ouvido),
            "confianca": float,
            "origem": str,
            "bloqueado": bool
        }
        """
        if not texto or not isinstance(texto, str): 
            return {"texto": "", "confianca": 0, "bloqueado": True}
        
        original = texto
        texto_limpo = texto.strip()
        texto_lower = texto_limpo.lower()

        with self._lock:
            ignored = self.ignored_phrases
            patterns = self.regex_patterns
            pmap = self.phonetic_map

        # 1. BLOQUEIO (Blacklist)
        if any(ign in texto_lower for ign in ignored):
            logger.info(f"🚫 Bloqueado: '{texto_limpo}'")
            return {"texto": texto_limpo, "confianca": 1.0, "bloqueado": True}

        if not texto_limpo: 
            return {"texto": "", "confianca": 0, "bloqueado": True}

        # 3. CORREÇÃO
        # A. Fuzzy/Inteligência Musical (Retorna Dict)
        try:
            # aplicar_fuzzy agora retorna um dicionário rico
            resultado_fuzzy = aplicar_fuzzy(texto_limpo, pmap)
            texto_processado = resultado_fuzzy["texto"]
            
            # B. Regex/Manual (Aplica sobre o resultado do fuzzy se necessário)
            # Geralmente o fuzzy já aplica o manual, mas o regex pega padrões complexos
            for pattern, callback in patterns:
                texto_processado = pattern.sub(callback, texto_processado)

            # Log de alteração
            if original != texto_processado:
                logger.info(f"⚡ Reflexo Final: '{original}' -> '{texto_processado}'")
            
            # Atualiza o texto final no objeto de resultado e retorna
            resultado_fuzzy["texto"] = texto_processado
            resultado_fuzzy["bloqueado"] = False
            return resultado_fuzzy

        except Exception as e:
            logger.error(f"⚠️ Erro reflexos: {e}")
            # Fallback seguro
            return {
                "texto": original, 
                "confianca": 0.0, 
                "origem": "erro", 
                "bloqueado": False
            }

    def corrigir_texto(self, texto: str) -> str:
        t, _ = self.processar_reflexo(texto)
        return t

    def adicionar_correcao(self, errado: str, correto: str) -> bool:
        if not errado or not correto: return False
        with self._lock:
            self.phonetic_map[errado.lower()] = correto
            if self.storage.salvar_manual(self.phonetic_map):
                self.reload()
                return True
        return False

# Singleton Global para uso em outros módulos
# A instância é criada normalmente, mas se for importada 2 vezes,
# o __new__ garantirá que a mesma seja reaproveitada.
reflexos = HipocampoReflexos()