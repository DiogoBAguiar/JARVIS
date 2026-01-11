import json
import re
import os
import logging
from typing import Dict, List, Optional

# Configuração de Logs Específica para o Módulo
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("HIPOCAMPO_REFLEXOS")

class IntentionNormalizer:
    """
    Módulo responsável pela correção fonética e normalização de intenções
    baseado em memória rápida (JSON) e padrões regex.
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
            
            # Pré-compilação de Regex para performance (evita recompilar a cada fala)
            self.regex_patterns = []
            for wrong, correct in raw_corrections.items():
                # Lookaround para garantir que não estamos substituindo parte de uma palavra correta
                # Ex: evitar que "toca" vire "toquea" se o padrão for "toc" -> "toque"
                pattern = re.compile(rf'\b{re.escape(wrong)}\b', re.IGNORECASE)
                self.regex_patterns.append((pattern, correct))
                
            self.blacklist = [re.compile(re.escape(p), re.IGNORECASE) for p in data.get("blacklisted_phrases", [])]
            
            logger.info(f"Memória de reflexos carregada. {len(self.regex_patterns)} padrões ativos.")
            
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Erro ao carregar memória de reflexos: {e}. Usando fallback vazio.")
            self.phonetic_map = {}
            self.regex_patterns = []
            self.blacklist = []

    def corrigir_texto(self, texto: str) -> str:
        """
        Aplica correções fonéticas instantâneas no texto transcrito.
        """
        if not texto or not isinstance(texto, str):
            return ""

        texto_processado = texto.strip()

        # 1. Filtro de Alucinações (Blacklist)
        for pattern in self.blacklist:
            if pattern.search(texto_processado):
                logger.warning(f"Alucinação de áudio detectada e descartada: '{texto_processado}'")
                return "" # Retorna vazio para descartar o comando

        # 2. Correção Fonética
        original = texto_processado
        try:
            for pattern, correction in self.regex_patterns:
                texto_processado = pattern.sub(correction, texto_processado)
            
            if original != texto_processado:
                logger.info(f"Reflexo acionado: '{original}' -> '{texto_processado}'")
                
        except Exception as e:
            logger.error(f"Erro durante processamento de regex: {e}. Retornando texto original.")
            return original

        return texto_processado

    def adicionar_correcao(self, errado: str, correto: str) -> bool:
        """Adiciona uma nova correção à memória persistente."""
        try:
            with open(self.config_file, 'r+', encoding='utf-8') as f:
                data = json.load(f)
                data["phonetic_corrections"][errado.lower()] = correto
                f.seek(0)
                json.dump(data, f, indent=4, ensure_ascii=False)
                f.truncate()
            
            # Recarrega memória
            self._load_memory()
            return True
        except Exception as e:
            logger.error(f"Falha ao persistir nova correção: {e}")
            return False