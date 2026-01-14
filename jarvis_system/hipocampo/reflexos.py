import json
import re
import os
import logging
from typing import Dict, List, Optional
from difflib import SequenceMatcher

# Configuração de Logs Específica para o Módulo
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("HIPOCAMPO_REFLEXOS")

class IntentionNormalizer:
    """
    Módulo responsável pela correção fonética e normalização de intenções
    baseado em memória rápida (JSON) e padrões regex + estatística (fuzzy).
    Atua como um filtro pré-cortical (antes da LLM).
    """
    
    def __init__(self, memory_path: str = "jarvis_system/data/reflexos_db"):
        self.memory_path = memory_path
        self.config_file = os.path.join(self.memory_path, "speech_config.json")
        self.phonetic_map: Dict[str, str] = {}
        self.regex_patterns: List[tuple] = []
        
        # Inicialização do subsistema
        self._ensure_memory_structure()
        self._load_memory()

    def _ensure_memory_structure(self) -> None:
        """Garante a existência da estrutura de diretórios e arquivos vitais."""
        try:
            if not os.path.exists(self.memory_path):
                os.makedirs(self.memory_path, exist_ok=True)
                logger.info(f"Diretório de memória criado: {self.memory_path}")

            if not os.path.exists(self.config_file):
                default_config = {
                    "phonetic_corrections": {
                        "freigilson": "Frei Gilson",
                        "sportfy": "Spotify",
                        "spotifai": "Spotify",
                        "potfari": "Spotify",  # <--- Adicionado para corrigir seu log
                        "abris": "abrir",      # <--- Adicionado para corrigir seu log
                        "toc": "toque",
                        "tok": "toque"
                    },
                    "blacklisted_phrases": [
                        "obrigado por assistir",
                        "legendas pela comunidade",
                        "subtitles by",
                        "amara.org"
                    ]
                }
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=4, ensure_ascii=False)
                logger.info("Configuração padrão de reflexos criada.")
        except OSError as e:
            logger.critical(f"Falha catastrófica ao criar estrutura de memória: {e}")
            raise

    def _load_memory(self) -> None:
        """Carrega e compila as correções fonéticas para memória RAM."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            raw_corrections = data.get("phonetic_corrections", {})
            self.phonetic_map = raw_corrections
            
            # Pré-compilação de Regex para performance
            self.regex_patterns = []
            for wrong, correct in raw_corrections.items():
                pattern = re.compile(rf'\b{re.escape(wrong)}\b', re.IGNORECASE)
                self.regex_patterns.append((pattern, correct))
                
            self.blacklist = [re.compile(re.escape(p), re.IGNORECASE) for p in data.get("blacklisted_phrases", [])]
            
            logger.info(f"Memória de reflexos carregada. {len(self.regex_patterns)} padrões ativos.")
            
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Erro ao carregar memória de reflexos: {e}. Usando fallback vazio.")
            self.phonetic_map = {}
            self.regex_patterns = []
            self.blacklist = []

    def _fuzzy_replace(self, texto: str, threshold=0.75) -> str:
        """Tenta encontrar trechos do texto que se assemelham estatisticamente."""
        texto_final = texto
        palavras = texto.split()
        if not palavras: return texto
        
        for errado, correto in self.phonetic_map.items():
            n_words = len(errado.split())
            for i in range(len(palavras) - n_words + 1):
                trecho_lista = palavras[i : i + n_words]
                trecho_str = " ".join(trecho_lista)
                
                similaridade = SequenceMatcher(None, trecho_str.lower(), errado.lower()).ratio()
                
                if similaridade >= threshold:
                    logger.info(f"✨ Correção Estatística: '{trecho_str}' ({similaridade:.2f}) -> '{correto}'")
                    texto_final = texto_final.replace(trecho_str, correto, 1)
                    palavras = texto_final.split()
                    break 
        return texto_final

    def corrigir_texto(self, texto: str) -> str:
        if not texto or not isinstance(texto, str): return ""
        texto_processado = texto.strip()

        for pattern in self.blacklist:
            if pattern.search(texto_processado): return ""

        original = texto_processado
        try:
            for pattern, correction in self.regex_patterns:
                texto_processado = pattern.sub(correction, texto_processado)
            
            texto_processado = self._fuzzy_replace(texto_processado)

            if original != texto_processado:
                logger.info(f"Reflexo acionado: '{original}' -> '{texto_processado}'")
                
        except Exception as e:
            logger.error(f"Erro: {e}")
            return original

        return texto_processado

    def adicionar_correcao(self, errado: str, correto: str) -> bool:
        try:
            with open(self.config_file, 'r+', encoding='utf-8') as f:
                data = json.load(f)
                data["phonetic_corrections"][errado.lower()] = correto
                f.seek(0)
                json.dump(data, f, indent=4, ensure_ascii=False)
                f.truncate()
            self._load_memory()
            return True
        except Exception as e:
            logger.error(f"Falha ao persistir: {e}")
            return False

# --- EXPORTAÇÃO SINGLETON (ESSENCIAL PARA O ORCHESTRATOR) ---
try:
    reflexos = IntentionNormalizer()
except Exception as e:
    logger.error(f"❌ Erro fatal ao iniciar Reflexos: {e}")
    reflexos = None