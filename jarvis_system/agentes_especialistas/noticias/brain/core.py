import logging
import json
from ..tools.search_engine import NewsEngine
from ..tools.reporter import NewsReporter # <--- Ferramenta de PDF adicionada

# --- IMPORTAÇÃO DOS PROMPTS CENTRALIZADOS ---
try:
    from . import prompts
except ImportError:
    prompts = None # Segurança caso o arquivo não exista

# Tenta importar o Classificador Semântico (Cérebro V2)
try:
    from .classifier import IntentRouter
except ImportError:
    IntentRouter = None 

# Tenta importar o Agno Local
try:
    from .llm_setup_noticias import LLMFactory 
    from agno.agent import Agent
except ImportError:
    LLMFactory = None
    Agent = None

logger = logging.getLogger("NEWS_BRAIN_JARVIS")

class NewsBrain:
    def __init__(self):
        self.engine = NewsEngine()
        self.reporter = NewsReporter() # <--- Inicializa o Gerador de Relatórios
        self.agent_llm = None
        
        # Inicializa o Roteador de Intenção
        if IntentRouter:
            self.router = IntentRouter()
        else:
            self.router = None
            logger.warning("⚠️ IntentRouter não encontrado.")

        # Inicializa o Analista (Agno)
        self._setup_analyst()

    def _setup_analyst(self):
        if LLMFactory and Agent:
            model = LLMFactory.get_model("llama-3.3-70b-versatile")
            if model:
                self.agent_llm = Agent(
                    model=model,
                    description="Você é J.A.R.V.I.S. Seja ultra-eficiente, polido e inteligente.",
                    markdown=False
                )

    def processar_solicitacao(self, user_input: str) -> str:
        """
        Orquestrador V3 (Mordomo):
        1. Classifica a Intenção e Complexidade.
        2. Coleta dados.
        3. Decide: Fala curta OU Fala curta + PDF detalhado.
        """
        
        # 1. CLASSIFICAÇÃO SEMÂNTICA
        if not self.router: return "Erro Crítico: Arquivo 'classifier.py' não encontrado."

        logger.info(f"🧠 Analisando intenção: '{user_input}'...")
        plano = self.router.classificar(user_input)
        
        intent = plano.get("intent", "investigacao")
        complexity = plano.get("complexity", "low")
        topico = plano.get("topic", user_input)
        fontes = plano.get("recommended_sources", [])
        
        logger.info(f"📋 Plano: {intent} | Complexidade: {complexity} | Fontes: {fontes}")

        # 2. COLETA MULTI-FONTE
        dados_coletados = self._executar_coleta(plano)

        if not dados_coletados:
            return f"Senhor, busquei informações sobre '{topico}', mas minhas fontes não retornaram dados satisfatórios no momento."

        # 3. DECISÃO DE FORMATO (Lógica Mordomo)
        # Gera PDF se for uma Análise profunda ou se o classificador marcou como "high" complexity
        gerar_pdf = (intent == "analise") or (complexity == "high")
        
        texto_fala = ""
        
        if gerar_pdf:
            return self._fluxo_com_pdf(topico, intent, dados_coletados)
        else:
            return self._fluxo_apenas_voz(topico, intent, dados_coletados)

    def _executar_coleta(self, plano):
        """Executa a busca definida no plano tático."""
        dados = []
        fontes = plano.get("recommended_sources", [])
        topico = plano.get("topic")
        
        # Busca Web
        if "web_search" in fontes or plano['intent'] in ["investigacao", "analise", "historia"]:
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
            return "Modo Offline: Assunto complexo detectado, mas estou sem LLM para gerar o relatório."

        # A) Gera texto técnico para o PDF (Modo 'relatorio')
        prompt_pdf = prompts.get_synthesis_prompt(topico, intent, json.dumps(dados, ensure_ascii=False), mode="relatorio")
        texto_pdf = self.agent_llm.run(prompt_pdf).content
        
        # B) Cria o arquivo físico
        caminho_pdf = self.reporter.criar_pdf(topico, texto_pdf, dados)
        
        # C) Gera o resumo verbal avisando do PDF (Modo 'voz')
        prompt_voz = prompts.get_synthesis_prompt(topico, intent, json.dumps(dados, ensure_ascii=False), mode="voz")
        resumo_voz = self.agent_llm.run(prompt_voz).content
        
        return f"{resumo_voz} (Senhor, compilei os detalhes técnicos e gráficos no relatório em: {caminho_pdf})"

    def _fluxo_apenas_voz(self, topico, intent, dados):
        """Apenas fala a resposta (Notícias rápidas)."""
        logger.info("🗣️ Assunto simples: Gerando resposta verbal direta...")
        
        if not self.agent_llm or not prompts:
            return f"Modo Offline: {len(dados)} notícias encontradas."

        prompt_voz = prompts.get_synthesis_prompt(topico, intent, json.dumps(dados, ensure_ascii=False), mode="voz")
        return self.agent_llm.run(prompt_voz).content