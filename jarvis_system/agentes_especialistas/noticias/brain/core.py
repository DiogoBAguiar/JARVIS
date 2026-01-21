import logging
import json
import re
from ..tools.search_engine import NewsEngine

# --- INTEGRAÇÃO COM AGNO LOCAL (NOTÍCIAS) ---
# Usa a fábrica local que criamos para não depender de arquivos globais por enquanto
try:
    from .llm_setup_noticias import LLMFactory 
    from agno.agent import Agent
except ImportError:
    LLMFactory = None
    Agent = None

logger = logging.getLogger("NEWS_BRAIN")

class NewsBrain:
    def __init__(self):
        self.engine = NewsEngine()
        self.agent_llm = None
        
        # Inicializa o LLM via Fábrica Local
        self._setup_llm()

        self.mapa_categorias = {
            "futebol": "futebol", "bola": "futebol", "jogo": "futebol", "flamengo": "futebol",
            "esporte": "esporte", "esportes": "esporte",
            "tech": "tecnologia", "tecnologia": "tecnologia", "celular": "tecnologia", "ia": "tecnologia",
            "crypto": "crypto", "bitcoin": "crypto", "cripto": "crypto",
            "economia": "economia", "dolar": "economia", "bolsa": "economia",
            "brasil": "geral", "geral": "geral", "manchetes": "geral", "noticias": "geral", "notícias": "geral",
            "paraiba": "paraiba", "joao pessoa": "paraiba", "local": "paraiba"
        }

    def _setup_llm(self):
        """Configura o Agente Agno usando o modelo local."""
        if LLMFactory and Agent:
            model = LLMFactory.get_model("llama-3.3-70b-versatile")
            if model:
                self.agent_llm = Agent(
                    model=model,
                    description="Você é um âncora de jornal experiente, objetivo e natural.",
                    markdown=False
                )
            else:
                logger.warning("⚠️ Fábrica não retornou modelo (verifique API KEYs).")

    def processar_solicitacao(self, user_input: str) -> str:
        # 1. LIMPEZA PRELIMINAR
        termo_clean = self._limpar_texto(user_input)
        
        # 2. ROTEAMENTO: RSS vs BUSCA
        categoria_detectada = self._detectar_categoria(termo_clean)
        
        noticias_raw = []
        modo = ""

        if categoria_detectada:
            logger.info(f"🧠 Rota definida: RSS ({categoria_detectada})")
            noticias_raw = self.engine.get_briefing(categoria=categoria_detectada)
            modo = "briefing"
        else:
            # Limpeza cirúrgica para busca
            termo_busca = self._limpar_para_busca(user_input)
            logger.info(f"🧠 Rota definida: BUSCA WEB ('{termo_busca}')")
            
            if len(termo_busca) < 3:
                return "Senhor, preciso de um tema mais específico para pesquisar."
                
            noticias_raw = self.engine.search_topic(termo_busca)
            modo = "investigacao"

        if not noticias_raw:
            return "Desculpe, senhor. Minhas fontes não retornaram nada relevante sobre isso no momento."

        # 3. SÍNTESE
        return self._sintetizar_com_llm(noticias_raw, modo, user_input)

    def _limpar_texto(self, texto):
        """Remove pontuação e deixa minúsculo."""
        return re.sub(r'[^\w\s]', '', texto.lower())

    def _limpar_para_busca(self, texto):
        """Remove stopwords para busca eficiente."""
        stopwords = ["jarvis", "o que", "quais", "as", "os", "novidades", "noticias", "sobre", "a", "e", "do", "da", "em", "recentemente", "hoje", "agora", "lancou"]
        palavras = self._limpar_texto(texto).split()
        palavras_uteis = [p for p in palavras if p not in stopwords]
        return " ".join(palavras_uteis)

    def _detectar_categoria(self, texto_limpo):
        tokens = texto_limpo.split()
        for token in tokens:
            if token in self.mapa_categorias:
                return self.mapa_categorias[token]
        return None

    def _sintetizar_com_llm(self, dados, modo, topico_original):
        """Gera o prompt e envia para o Agno."""
        
        # Fallback se Agno não estiver ativo
        if not self.agent_llm:
            return f"Simulação (Offline): Encontrei {len(dados)} notícias. Manchete: {dados[0].get('titulo')}"

        contexto_dados = json.dumps(dados, indent=2, ensure_ascii=False)
        
        if modo == "briefing":
            instrucao = "O usuário pediu um resumo rápido. Crie um texto curto (máximo 3 frases) conectando as notícias. Seja natural."
        else:
            instrucao = f"O usuário perguntou sobre: '{topico_original}'. Explique o contexto com base nos dados abaixo. Seja direto."

        prompt_final = f"""
        INSTRUÇÃO: {instrucao}
        DADOS RECEBIDOS: {contexto_dados}
        SAÍDA (Texto puro em PT-BR para TTS):
        """
        
        try:
            # Agno executa e retorna o objeto RunResponse
            response = self.agent_llm.run(prompt_final)
            return response.content
        except Exception as e:
            logger.error(f"Erro no LLM: {e}")
            return "Tive um problema ao gerar o resumo das notícias, senhor."