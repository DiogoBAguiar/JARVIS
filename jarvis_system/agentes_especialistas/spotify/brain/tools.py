import logging
from typing import Optional

logger = logging.getLogger("SPOTIFY_TOOLS")

class SpotifyToolkit:
    """
    Conjunto de ferramentas que a IA pode utilizar.
    Cada método aqui vira uma 'Tool' para o Agno/LLM.
    """

    def __init__(self, controller, consciencia=None):
        self.controller = controller
        self.consciencia = consciencia

    def iniciar_aplicativo(self) -> str:
        """Abre o Spotify. Use se o usuário disser 'abrir', 'iniciar'."""
        try:
            if self.controller.launch_app():
                return "Spotify iniciado e pronto."
            return "Falha ao iniciar o processo do Spotify."
        except Exception as e:
            return f"Erro técnico ao abrir: {e}"

    def tocar_musica(self, nome_musica: str) -> str:
        """Toca uma música ou artista específico. Ex: 'Tocar Metallica'."""
        try:
            return self.controller.play_search(nome_musica)
        except Exception as e:
            return f"Erro ao tentar tocar: {e}"

    def pausar_ou_continuar(self) -> str:
        """Pausa ou continua a reprodução atual."""
        self.controller.resume()
        return "Play/Pause acionado."

    def proxima_faixa(self) -> str:
        """Pula para a próxima música."""
        self.controller.next_track()
        return "Próxima faixa."

    def faixa_anterior(self) -> str:
        """Volta para a música anterior."""
        self.controller.previous_track()
        return "Faixa anterior."

    def consultar_memoria_musical(self, descricao: str) -> str:
        """
        Busca na base vetorial pessoal (músicas favoritas/histórico).
        Útil quando o usuário diz 'toque algo que eu gosto'.
        """
        try:
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