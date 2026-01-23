import logging
import json
from .llm_setup_noticias import LLMFactory
from agno.agent import Agent

logger = logging.getLogger("NEWS_CLASSIFIER")

class IntentRouter:
    def __init__(self):
        self.agent = None
        self._setup_classifier()

    def _setup_classifier(self):
        """Configura um Agente leve focado APENAS em classificação JSON."""
        model = LLMFactory.get_model("llama-3.3-70b-versatile")
        if model:
            self.agent = Agent(
                model=model,
                description="Você é um classificador semântico de intenções de notícias.",
                markdown=False
            )

    def classificar(self, user_input: str) -> dict:
        """
        Transforma 'Bitcoin vai cair?' em:
        {
            "intent": "analise",
            "topic": "bitcoin price trend",
            "sources": ["search", "crypto_rss"],
            "timeframe": "short_term"
        }
        """
        if not self.agent:
            return {"intent": "erro", "reason": "LLM offline"}

        prompt = f"""
        Analise a entrada do usuário e retorne UM JSON (sem markdown) com este schema:
        {{
            "intent": "briefing" | "investigacao" | "analise" | "historia",
            "topic": "termo principal de busca em portugues",
            "search_term": "termo otimizado para busca web (ex: 'bitcoin price analysis')",
            "recommended_sources": ["rss_geral" | "rss_crypto" | "rss_tech" | "rss_esporte" | "web_search"],
            "complexity": "low" | "high"
        }}

        REGRAS DE INTENÇÃO:
        - "briefing": Resumo geral, "novidades", "o que está acontecendo".
        - "investigacao": Fato específico, "o que aconteceu com X", "lançamento Y".
        - "analise": Perguntas de "por que", "vai subir/cair", "causas", "impactos".
        - "historia": "quem foi", "quando surgiu", contexto antigo.

        ENTRADA USUÁRIO: "{user_input}"
        
        SAÍDA JSON:
        """
        
        try:
            response = self.agent.run(prompt)
            # Limpeza básica caso o LLM mande ```json ... ```
            clean_json = response.content.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_json)
        except Exception as e:
            logger.error(f"Erro na classificação: {e}")
            # Fallback seguro
            return {"intent": "investigacao", "topic": user_input, "recommended_sources": ["web_search"]}