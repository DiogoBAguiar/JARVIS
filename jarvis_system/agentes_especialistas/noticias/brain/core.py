import logging
import json
from ..tools.search_engine import NewsEngine
from ..tools.reporter import NewsReporter

# --- IMPORTAÇÃO DOS PROMPTS CENTRALIZADOS ---
try:
    from . import prompts
except ImportError:
    prompts = None 

# Tenta importar dependências opcionais
try:
    from .classifier import IntentRouter
except ImportError:
    IntentRouter = None 

try:
    from .llm_setup_noticias import LLMFactory, SafeAgent, MockAgent
    from agno.agent import Agent
except ImportError:
    LLMFactory = None
    Agent = None
    SafeAgent = None
    MockAgent = None

logger = logging.getLogger("NEWS_BRAIN_JARVIS")

class NewsBrain:
    def __init__(self):
        self.engine = NewsEngine()
        self.reporter = NewsReporter()
        self.agent_llm = None
        
        # Inicializa o Roteador de Intenção
        if IntentRouter:
            self.router = IntentRouter()
        else:
            self.router = None
            logger.warning("⚠️ IntentRouter não encontrado.")

        # Inicializa o Analista (Agno) com Segurança
        self._setup_analyst()

    def _setup_analyst(self):
        """
        Configura o Agente Analista usando o SafeAgent.
        """
        if LLMFactory and Agent and SafeAgent:
            model = LLMFactory.get_model("llama-3.3-70b-versatile")
            
            if model:
                real_agent = Agent(
                    model=model,
                    description="Analista J.A.R.V.I.S.",
                    markdown=False
                )
                self.agent_llm = SafeAgent(real_agent)
                # logger.info("🧠 Analista J.A.R.V.I.S. Online")
            else:
                logger.warning("⚠️ Sem chaves de API. Iniciando em Modo Simulação (Mock).")
                self.agent_llm = MockAgent()
        elif MockAgent:
             self.agent_llm = MockAgent()

    def processar_solicitacao(self, user_input: str) -> str:
        """
        Orquestrador V3 (Mordomo):
        """
        if not self.router: return "Erro Crítico: Arquivo 'classifier.py' não encontrado."

        logger.info(f"🧠 Analisando intenção: '{user_input}'...")
        
        # 1. CLASSIFICAÇÃO (Com proteção contra retorno None/Vazio)
        plano = self.router.classificar(user_input)
        if not plano: plano = {} # Garante que seja dict
        
        # Extração segura com defaults
        intent = plano.get("intent", "investigacao")
        complexity = plano.get("complexity", "low")
        topico = plano.get("topic", user_input)
        fontes = plano.get("recommended_sources", [])
        
        logger.info(f"📋 Plano: {intent} | Complexidade: {complexity} | Fontes: {fontes}")

        # 2. COLETA MULTI-FONTE
        dados_coletados = self._executar_coleta(plano, user_input)

        # Se não achou dados (e não é simulação forçada), avisa
        if not dados_coletados:
             # Se for MockAgent, ele inventa, então prossegue. 
             # Se for Real e vazio, retorna aviso.
             is_mock = False
             try:
                 if isinstance(self.agent_llm, MockAgent): is_mock = True
                 if hasattr(self.agent_llm, 'mock') and self.agent_llm.agent is None: is_mock = True
             except: pass
             
             if not is_mock and "simulacao" not in topico.lower():
                 return f"Senhor, busquei informações sobre '{topico}', mas minhas fontes não retornaram dados satisfatórios no momento."

        # 3. DECISÃO DE FORMATO
        gerar_pdf = (intent == "analise") or (complexity == "high")
        
        if gerar_pdf:
            return self._fluxo_com_pdf(topico, intent, dados_coletados)
        else:
            return self._fluxo_apenas_voz(topico, intent, dados_coletados)

    def _executar_coleta(self, plano, user_input_fallback=""):
        """Executa a busca definida no plano tático."""
        dados = []
        # Garante lista mesmo se plano falhar
        fontes = plano.get("recommended_sources", [])
        topico = plano.get("topic", user_input_fallback)
        
        # CORREÇÃO DO ERRO KEYERROR 'intent'
        # Usamos .get() para não quebrar se a chave faltar
        intent_val = plano.get('intent', 'investigacao')
        
        # Busca Web
        if "web_search" in fontes or intent_val in ["investigacao", "analise", "historia"]:
            termo = plano.get("search_term", topico)
            logger.info(f"🌍 Executando Busca Web: '{termo}'...")
            dados += self.engine.search_topic(termo)
            
        # RSS
        for fonte in fontes:
            if "rss_" in fonte:
                cat = fonte.replace("rss_", "")
                logger.info(f"📡 RSS Especializado: {cat}")
                dados += self.engine.get_briefing(categoria=cat, limit=3)
        
        return dados

    def _fluxo_com_pdf(self, topico, intent, dados):
        """Gera relatório escrito e avisa verbalmente."""
        logger.info("📄 Assunto complexo: Gerando Relatório Detalhado (PDF)...")
        
        if not self.agent_llm or not prompts:
            return "Modo Offline: Sem LLM para gerar o relatório."

        # A) Gera texto técnico para o PDF
        prompt_pdf = prompts.get_synthesis_prompt(topico, intent, json.dumps(dados, ensure_ascii=False), mode="relatorio")
        
        # Tratamento de resposta (seja Real ou Mock)
        resp_obj = self.agent_llm.run(prompt_pdf)
        texto_pdf = resp_obj.content if hasattr(resp_obj, 'content') else str(resp_obj)
        
        # B) Cria o arquivo físico
        # 
        caminho_pdf = self.reporter.criar_pdf(topico, texto_pdf, dados)
        
        # C) Gera o resumo verbal
        prompt_voz = prompts.get_synthesis_prompt(topico, intent, json.dumps(dados, ensure_ascii=False), mode="voz")
        resp_voz = self.agent_llm.run(prompt_voz)
        resumo_voz = resp_voz.content if hasattr(resp_voz, 'content') else str(resp_voz)
        
        return f"{resumo_voz} (Senhor, compilei os detalhes técnicos e gráficos no relatório em: {caminho_pdf})"

    def _fluxo_apenas_voz(self, topico, intent, dados):
        """Apenas fala a resposta."""
        logger.info("🗣️ Assunto simples: Gerando resposta verbal direta...")
        
        if not self.agent_llm or not prompts:
            return f"Modo Offline: {len(dados)} notícias encontradas."

        prompt_voz = prompts.get_synthesis_prompt(topico, intent, json.dumps(dados, ensure_ascii=False), mode="voz")
        
        resp_obj = self.agent_llm.run(prompt_voz)
        return resp_obj.content if hasattr(resp_obj, 'content') else str(resp_obj)