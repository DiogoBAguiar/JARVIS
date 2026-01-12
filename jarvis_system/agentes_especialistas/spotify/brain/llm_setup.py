import os
import logging
from typing import Optional

# Tenta importar o Agno, mas não quebra se falhar (permite fallback)
try:
    from agno.models.google import Gemini
    from agno.models.groq import Groq
    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False

logger = logging.getLogger("SPOTIFY_BRAIN_LLM")

class LLMFactory:
    """Fábrica de Modelos Cognitivos (Gerencia conexões com APIs)."""

    @staticmethod
    def get_model(preferred_model: str):
        if not AGNO_AVAILABLE:
            logger.error("Agno Framework não instalado.")
            return None

        groq_key = os.getenv("GROQ_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")

        # 1. Tenta Groq (Geralmente mais rápido para comandos)
        if ("llama" in preferred_model.lower() or "mixtral" in preferred_model.lower()) and groq_key:
            logger.info(f"🧠 Motor Cognitivo Ativo: Groq ({preferred_model})")
            return Groq(id=preferred_model, api_key=groq_key)
        
        # 2. Fallback para Gemini (Mais estável/inteligente)
        if gemini_key:
            logger.info("🧠 Motor Cognitivo Ativo: Gemini 1.5 Flash")
            return Gemini(id="gemini-1.5-flash", api_key=gemini_key)
        
        logger.warning("⚠️ Nenhuma chave de API válida encontrada (GROQ ou GEMINI).")
        return None