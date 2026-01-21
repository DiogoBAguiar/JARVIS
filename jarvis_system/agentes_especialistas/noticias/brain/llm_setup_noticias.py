import os
import logging
from typing import Optional

# Tenta importar o Agno
try:
    from agno.models.google import Gemini
    from agno.models.groq import Groq
    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False

logger = logging.getLogger("NEWS_BRAIN_LLM")

class LLMFactory:
    """
    Fábrica de Modelos Cognitivos (Específica para Notícias).
    """

    @staticmethod
    def get_model(preferred_model: str = "llama-3.3-70b-versatile"):
        if not AGNO_AVAILABLE:
            logger.error("❌ Agno Framework não instalado. Instale com: pip install agno")
            return None

        groq_key = os.getenv("GROQ_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")

        # 1. Prioridade: Groq (Rápido e excelente para síntese de texto)
        if groq_key:
            logger.info(f"🧠 [News] Motor Cognitivo Ativo: Groq ({preferred_model})")
            return Groq(id=preferred_model, api_key=groq_key)
        
        # 2. Fallback: Gemini
        if gemini_key:
            logger.info("🧠 [News] Motor Cognitivo Ativo: Gemini 1.5 Flash")
            return Gemini(id="gemini-1.5-flash", api_key=gemini_key)
        
        logger.warning("⚠️ Nenhuma chave de API válida encontrada (GROQ ou GEMINI).")
        return None