import logging
import json
import re

# Tenta importar as dependências e os agentes de segurança
try:
    from .llm_setup_noticias import LLMFactory, SafeAgent, MockAgent
    from agno.agent import Agent
except ImportError:
    LLMFactory = None
    Agent = None
    SafeAgent = None
    MockAgent = None

logger = logging.getLogger("NEWS_CLASSIFIER")

class IntentRouter:
    def __init__(self):
        self.agent = None
        self._setup_classifier()

    def _setup_classifier(self):
        """
        Configura o Agente Classificador com proteção (SafeAgent).
        Se a API estiver indisponível ou estourar a cota (429), usa o Mock.
        """
        if LLMFactory and Agent and SafeAgent:
            # Modelo versátil para classificação precisa
            model = LLMFactory.get_model("llama-3.3-70b-versatile")
            
            if model:
                real_agent = Agent(
                    model=model,
                    description="Você é um classificador semântico de intenções de notícias. Retorne apenas JSON.",
                    markdown=False
                )
                # 🛡️ ENVOLVE NO WRAPPER DE SEGURANÇA
                # Isso garante a troca automática para o Mock se a API falhar
                self.agent = SafeAgent(real_agent)
            else:
                # Se não conseguiu modelo (sem chave), usa Mock direto
                self.agent = MockAgent()
        elif MockAgent:
            # Se não tem biblioteca Agno instalada
            self.agent = MockAgent()

    def classificar(self, user_input: str) -> dict:
        """
        Analisa a frase do usuário e define o plano de ação (JSON).
        Retorna: {intent, topic, search_term, recommended_sources, complexity}
        """
        # Plano de emergência (Fallback) caso tudo falhe (inclusive o Mock)
        default_plan = {
            "intent": "investigacao", 
            "topic": user_input, 
            "search_term": user_input,
            "recommended_sources": ["web_search"],
            "complexity": "low"
        }

        if not self.agent:
            return default_plan

        # Prompt otimizado para forçar saída JSON
        prompt = f"""
        Analise a entrada do usuário e retorne ESTRITAMENTE UM JSON com este schema:
        {{
            "intent": "briefing" | "investigacao" | "analise" | "historia",
            "topic": "Tópico principal em português",
            "search_term": "Termo otimizado para busca (ex: 'bitcoin price analysis')",
            "recommended_sources": ["web_search", "rss_geral", "rss_crypto", "rss_tech", "rss_esporte", "rss_games", "rss_otaku"],
            "complexity": "low" | "high"
        }}

        REGRAS DE COMPLEXIDADE:
        1. Se o usuário pedir "análise", "relatório", "detalhado", "dossiê" ou "comparativo", MARQUE "complexity": "high".
        2. Se o tópico for financeiro (Crypto, Bitcoin, Juros, Dólar), MARQUE "complexity": "high".
        3. Se for apenas "notícias de hoje" ou "resumo", use "complexity": "low".

        ENTRADA USUÁRIO: "{user_input}"
        
        SAÍDA JSON:
        """
        
        try:
            # O SafeAgent gerencia a chamada. 
            # Se a API estiver OK -> Retorna JSON real.
            # Se der erro 429 -> Chama MockAgent -> Lê mocks.json -> Retorna o JSON do cenário correspondente.
            response_obj = self.agent.run(prompt)
            
            # Extrai o texto (compatibilidade entre Agno Response e MockResponse)
            content = response_obj.content if hasattr(response_obj, 'content') else str(response_obj)
            
            # Limpeza cirúrgica do JSON
            clean_json = self._limpar_json(content)
            
            if not clean_json:
                return default_plan

            return json.loads(clean_json)

        except Exception as e:
            logger.error(f"Erro na classificação: {e}")
            return default_plan

    def _limpar_json(self, text):
        """Remove markdown (```json) e sujeira antes/depois do JSON."""
        if not text: return "{}"
        
        # Remove blocos de código markdown
        text = text.replace("```json", "").replace("```", "")
        
        # Tenta encontrar o início e fim do objeto JSON para ignorar texto extra
        start = text.find("{")
        end = text.rfind("}") + 1
        
        if start != -1 and end != -1:
            return text[start:end]
        
        return text.strip()