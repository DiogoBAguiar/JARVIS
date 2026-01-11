import os
import logging
from typing import Optional, Any

# Framework Cognitivo (Agno)
try:
    from agno.agent import Agent
    from agno.models.google import Gemini
    from agno.models.groq import Groq
except ImportError:
    # Fallback crítico se o framework não estiver instalado
    raise ImportError("Framework 'agno' não encontrado. Instale as dependências.")

from .controller import SpotifyController

# Configuração de Logs
logger = logging.getLogger("SPOTIFY_NLU")

class SpotifyAgnoAgent:
    """
    Córtex Especialista em Música.
    Traduz intenção natural (pt-BR) em comandos mecânicos para o Controller.
    Possui tolerância a falhas de API (Fallback Local) e erros de execução.
    """

    def __init__(self):
        try:
            self.controller = SpotifyController()
        except Exception as e:
            logger.critical(f"Falha ao iniciar Controller: {e}")
            self.controller = None # O agente tentará operar em modo degradado ou avisar erro

        self.model_name = os.getenv("JARVIS_MODEL_CLOUD", "gemini-1.5-flash")
        self.agent = self._configurar_agente()

    def _get_llm_instance(self):
        """Seleção dinâmica de LLM com fallback de configuração."""
        groq_key = os.getenv("GROQ_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")

        # Preferência por Groq (Llama) se configurado e solicitado
        if ("llama" in self.model_name.lower() or "mixtral" in self.model_name.lower()) and groq_key:
            logger.info(f"Usando motor cognitivo: Groq ({self.model_name})")
            return Groq(id=self.model_name, api_key=groq_key)
        
        # Fallback para Gemini
        if gemini_key:
            logger.info("Usando motor cognitivo: Gemini 1.5 Flash")
            return Gemini(id="gemini-1.5-flash", api_key=gemini_key)
        
        # Último recurso: lança erro para ser tratado acima
        logger.warning("Nenhuma chave de API de LLM encontrada (GROQ ou GEMINI).")
        return None

    def _configurar_agente(self) -> Optional[Agent]:
        llm = self._get_llm_instance()
        if not llm:
            return None

        # --- FERRAMENTAS BLINDADAS (Safe Tools) ---
        # Cada ferramenta captura suas próprias falhas para informar a LLM sem quebrar o fluxo.

        def iniciar_aplicativo() -> str:
            """Abre o Spotify. Use se o usuário disser 'abrir', 'iniciar'."""
            if not self.controller: return "Erro interno: Controlador inativo."
            try:
                if self.controller.launch_app():
                    return "Spotify iniciado e pronto."
                return "Falha ao iniciar o processo do Spotify."
            except Exception as e:
                logger.error(f"Erro na tool iniciar_aplicativo: {e}")
                return f"Erro técnico ao abrir: {e}"

        def consultar_memoria_musical(descricao: str) -> str:
            """Busca na base vetorial pessoal (músicas favoritas/histórico)."""
            try:
                # Importação lazy e segura
                from jarvis_system.hipocampo.curador_musical import CuradorMusical
                curador = CuradorMusical()
                resultados = curador.buscar_vetorial(descricao, top_k=1)
                if resultados:
                    return f"Encontrei na memória: '{resultados[0]}'. Tente tocar isso."
                return "Nada relevante encontrado na memória pessoal."
            except ImportError:
                return "Módulo de memória musical não instalado."
            except Exception as e:
                logger.error(f"Erro na tool memoria: {e}")
                return "Erro ao consultar memória."

        def tocar_musica(nome_musica: str) -> str:
            """Toca uma música/artista específico."""
            if not self.controller: return "Erro controlador."
            try:
                return self.controller.play_search(nome_musica)
            except Exception as e:
                return f"Erro ao tentar tocar: {e}"

        def clicar_elemento(texto_alvo: str) -> str:
            """Clica visualmente em um texto na tela."""
            if not self.controller: return "Erro controlador."
            try:
                sucesso = self.controller.buscar_e_clicar(texto_alvo)
                return "Clique efetuado." if sucesso else "Elemento não encontrado na tela."
            except Exception as e:
                return f"Erro visual: {e}"

        # Wrappers simples com proteção
        def controle_midia(acao: str) -> str:
            """Controle genérico: pausar, continuar, proxima, anterior."""
            if not self.controller: return "Erro controlador."
            try:
                if acao == "pausar" or acao == "continuar": self.controller.resume()
                elif acao == "proxima": self.controller.next_track()
                elif acao == "anterior": self.controller.previous_track()
                return f"Ação '{acao}' enviada."
            except Exception as e:
                return f"Erro de controle: {e}"

        # Mapeamento para tools do Agno
        def pausar_ou_continuar(): return controle_midia("pausar")
        def proxima_faixa(): return controle_midia("proxima")
        def faixa_anterior(): return controle_midia("anterior")
        
        def rolar_tela(direcao: str = "down"):
            if self.controller: self.controller.scroll(direcao); return f"Rolagem {direcao}."
            return "Erro controlador."

        return Agent(
            model=llm,
            description="Você é o Jarvis DJ. Controle o Spotify com precisão.",
            instructions=[
                "Se o usuário pedir música vaga, consulte a memória primeiro.",
                "Se pedir para abrir, use iniciar_aplicativo.",
                "Para tocar, use tocar_musica.",
                "Se falhar, explique o motivo.",
                "Responda de forma muito breve (máx 1 frase)."
            ],
            tools=[
                iniciar_aplicativo, consultar_memoria_musical, tocar_musica,
                clicar_elemento, pausar_ou_continuar, proxima_faixa,
                faixa_anterior, rolar_tela
            ],
            markdown=True,
            debug_mode=False # Desativado para produção
        )

    def _fallback_de_emergencia(self, comando: str) -> str:
        """Sistema Límbico: Reage quando o Córtex Frontal (LLM) falha."""
        if not self.controller: return "Sistema de controle inoperante."
        
        cmd = comando.lower().strip()
        logger.warning(f"⚠️ Ativando Fallback Local para: '{cmd}'")

        try:
            if any(x in cmd for x in ["abrir", "iniciar", "lançar"]) and "spotify" in cmd:
                self.controller.launch_app()
                return "Abrindo Spotify (Modo Offline)."

            if "proxima" in cmd or "pular" in cmd:
                self.controller.next_track()
                return "Próxima (Offline)."
            
            if "pausa" in cmd or "parar" in cmd or "continuar" in cmd:
                self.controller.resume()
                return "Play/Pause (Offline)."

            # Tentativa de extração de música "na força bruta"
            # Remove gatilhos comuns para isolar o nome da música
            gatilhos = ["tocar", "toque", "play", "ouve", "ouvir", "bota", "coloca", "no spotify"]
            termo_limpo = cmd
            for g in gatilhos:
                termo_limpo = termo_limpo.replace(g, "")
            
            termo_limpo = termo_limpo.strip()
            
            if termo_limpo and len(termo_limpo) > 2:
                self.controller.play_search(termo_limpo)
                return f"Buscando '{termo_limpo}' (Modo Offline)..."

        except Exception as e:
            logger.error(f"Erro no fallback: {e}")
            return "Erro crítico no modo de emergência."

        return "Não compreendi o comando (e a IA está offline)."

    def processar(self, comando: str) -> str:
        """Entrada principal do Agente."""
        if not comando: return ""
        
        # Se o agente não foi configurado (sem API Key), vai direto pro fallback
        if not self.agent:
            return self._fallback_de_emergencia(comando)

        try:
            logger.info(f"🧠 Processando intenção: '{comando}'")
            # Run do Agno
            resposta = self.agent.run(comando)
            
            # Extração segura do conteúdo
            conteudo = ""
            if hasattr(resposta, 'content'):
                conteudo = resposta.content
            else:
                conteudo = str(resposta)
            
            return conteudo

        except Exception as e:
            logger.error(f"🔥 Falha Cognitiva (LLM): {e}")
            # Se for erro de API, Rate Limit ou Modelo sobrecarregado -> Fallback
            return self._fallback_de_emergencia(comando)