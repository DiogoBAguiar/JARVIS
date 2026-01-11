import os
import re
from typing import Optional

# Framework Agno e Modelos Suportados
from agno.agent import Agent
from agno.models.google import Gemini
from agno.models.groq import Groq

# Importamos o Controller
from .controller import SpotifyController

class SpotifyAgnoAgent:
    def __init__(self):
        self.controller = SpotifyController()
        # Lê o modelo do .env (ex: llama-3.3-70b-versatile)
        self.model_name = os.getenv("JARVIS_MODEL_CLOUD", "gemini-1.5-flash")
        self.agent = self._configurar_agente()

    def _get_llm_instance(self):
        """Fábrica de LLMs: Decide qual driver usar."""
        # Se for modelo Llama/Mixtral -> Groq
        if "llama" in self.model_name.lower() or "mixtral" in self.model_name.lower():
            api_key = os.getenv("GROQ_API_KEY")
            if api_key:
                return Groq(id=self.model_name, api_key=api_key)
        
        # Padrão -> Gemini
        return Gemini(id="gemini-1.5-flash", api_key=os.getenv("GEMINI_API_KEY"))

    def _configurar_agente(self) -> Agent:
        
        # --- DEFINIÇÃO DAS FERRAMENTAS (TOOLS) ---

        def iniciar_aplicativo():
            """
            Use APENAS quando o usuário pedir explicitamente para 'abrir', 'iniciar' ou 'lançar' o Spotify.
            Não use para tocar músicas, apenas para abrir a janela do aplicativo.
            """
            self.controller.launch_app()
            return "Spotify inicializado."

        def consultar_memoria_musical(descricao: str):
            """
            Use para buscar músicas no banco de dados pessoal do usuário (1000+ músicas/vetores).
            Útil quando o usuário pede algo vago como 'toca aquela triste do Linkin Park', 
            'música do ano 2005' ou 'algo para relaxar'.
            """
            try:
                # Importação tardia para evitar ciclo e só carregar se necessário
                from jarvis_system.hipocampo.curador_musical import CuradorMusical
                curador = CuradorMusical()
                
                # Assume que o curador tem busca vetorial implementada
                # Se não tiver, ele vai cair no except e o Jarvis segue a vida
                resultados = curador.buscar_vetorial(descricao, top_k=1)
                
                if resultados:
                    # Retorna algo como "Numb - Linkin Park"
                    return f"Encontrei na biblioteca pessoal: {resultados[0]}. Use a ferramenta 'tocar_musica' com este nome."
                return "Não encontrei nada específico na biblioteca local."
            except Exception as e:
                return f"Erro ao consultar memória: {e}"

        def tocar_musica(nome_musica: str):
            """
            Busca e toca uma música específica.
            Args:
                nome_musica (str): O nome da música ou artista. Ex: "Linkin Park", "Rock".
            """
            return self.controller.play_search(nome_musica)

        def clicar_elemento(texto_alvo: str):
            """Clica em botões ou textos na tela."""
            sucesso = self.controller.buscar_e_clicar(texto_alvo)
            return "Clique realizado." if sucesso else f"Não encontrei '{texto_alvo}'."

        def pausar_ou_continuar():
            """Pausa ou retoma a música."""
            self.controller.resume()
            return "Feito."

        def proxima_faixa():
            """Pula para a próxima música."""
            self.controller.next_track()
            return "Próxima."

        def faixa_anterior():
            """Volta para a música anterior."""
            self.controller.previous_track()
            return "Voltei."

        def rolar_tela(direcao: str = "down"):
            """Rola a tela ('down' ou 'up')."""
            self.controller.scroll(direcao)
            return f"Rolei {direcao}."

        def gerar_relatorio_biblioteca():
            """Gera relatório da biblioteca."""
            try:
                from jarvis_system.hipocampo.curador_musical import CuradorMusical
                CuradorMusical().gerar_relatorio()
                return "Relatório gerado."
            except Exception as e:
                return f"Erro: {e}"

        # --- CONFIGURAÇÃO DO AGENTE ---
        return Agent(
            model=self._get_llm_instance(),
            description="Você é o Agente DJ do Jarvis.",
            instructions=[
                "Controle o Spotify via visão e teclado.",
                "1. Se o usuário pedir para 'abrir' o app, use 'iniciar_aplicativo' IMEDIATAMENTE.",
                "2. Se o pedido for vago (ex: 'aquela música boa'), use 'consultar_memoria_musical' primeiro.",
                "3. Se o usuário disser apenas 'tocar' sem nome, pergunte 'O que deseja ouvir?'.",
                "4. Para tocar músicas específicas, use 'tocar_musica'.",
                "Seja conciso."
            ],
            tools=[
                iniciar_aplicativo,        # Prioridade Alta
                consultar_memoria_musical, # Prioridade Alta para contexto
                tocar_musica, 
                clicar_elemento, 
                pausar_ou_continuar, 
                proxima_faixa, 
                faixa_anterior, 
                rolar_tela, 
                gerar_relatorio_biblioteca
            ],
            markdown=True,
            debug_mode=True
        )

    def _fallback_de_emergencia(self, comando: str) -> str:
        """Lógica 'manual' para falhas de API."""
        cmd = comando.lower()
        print("⚠️ [NLU] Modo de Emergência (Offline).")

        # Fallback inteligente: Tenta abrir se pedir abrir
        if "abrir" in cmd and "spotify" in cmd:
            self.controller.launch_app()
            return "Modo Offline: Abrindo Spotify..."

        if "tocar" in cmd or "play" in cmd:
            termo = cmd.replace("tocar", "").replace("play", "").replace("abrir", "").replace("spotify", "").strip()
            if not termo: termo = "Daily Mix 1"
            
            self.controller.play_search(termo)
            return f"Modo Offline: Buscando '{termo}'..."
        
        elif "pausa" in cmd:
            self.controller.pause()
            return "Pausado."
        
        elif "proxima" in cmd:
            self.controller.next_track()
            return "Próxima."
            
        return "Comando não compreendido no modo offline."

    def processar(self, comando: str) -> str:
        try:
            resposta = self.agent.run(comando)
            if hasattr(resposta, 'content'):
                return resposta.content
            return str(resposta)
            
        except Exception as e:
            erro_str = str(e)
            # Fallback para erros de API (400, 429, 500)
            if "400" in erro_str or "429" in erro_str or "tool_use_failed" in erro_str:
                return self._fallback_de_emergencia(comando)
            
            return f"Erro crítico: {erro_str}"