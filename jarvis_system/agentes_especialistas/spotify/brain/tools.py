import logging
from typing import Optional

# Importação da nova fachada modular de Memória Musical
from jarvis_system.hipocampo.pensamento_musical import CuradorMusical

logger = logging.getLogger("SPOTIFY_TOOLS")

class SpotifyToolkit:
    """
    Conjunto de ferramentas que a IA pode utilizar.
    Conecta o Cérebro ao Corpo (Controller) e à Memória (Curador).
    """

    def __init__(self, controller, consciencia=None):
        self.controller = controller
        self.consciencia = consciencia
        
        # Instancia o Curador Musical (Conexão com o Hipocampo)
        # Isso permite acesso ao banco de dados e à lógica de correção
        self.curador = CuradorMusical()

    # --- MÉTODOS DE INTELIGÊNCIA (Novos) ---

    def verificar_se_artista(self, termo: str) -> bool:
        """
        Verifica se o termo é um Artista no banco de dados local.
        Usado pelo Brain para decidir se clica no filtro 'Artistas'.
        """
        return self.curador.existe_artista(termo)
    
    def sugerir_correcao(self, termo: str) -> Optional[str]:
        """
        Tenta corrigir foneticamente o termo usando o banco de dados.
        Ex: 'Freio Gil Som' -> 'Frei Gilson'
        """
        # Delega para a fachada do curador (que usa o search engine)
        return self.curador.sugerir_correcao(termo)

    # --- MÉTODOS DE AÇÃO (Controller) ---

    def iniciar_aplicativo(self) -> str:
        """Abre o Spotify. Use se o usuário disser 'abrir', 'iniciar'."""
        try:
            if self.controller.launch_app():
                return "Spotify iniciado e pronto."
            return "Falha ao iniciar o processo do Spotify."
        except Exception as e:
            return f"Erro técnico ao abrir: {e}"

    def tocar_musica(self, nome_musica: str, tipo: str = "musica") -> str:
        """
        Toca uma música ou artista específico.
        Args:
            nome_musica: O termo de busca.
            tipo: 'musica' ou 'artista' (Define qual filtro visual usar).
        """
        try:
            # Tenta passar o 'tipo' se o controller suportar (nossa atualização do visual_navigator)
            try:
                return self.controller.play_search(nome_musica, tipo=tipo)
            except TypeError:
                # Fallback se o controller.py não tiver sido atualizado para aceitar kwargs
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
            # Usa a instância já criada no __init__
            resultados = self.curador.buscar_vetorial(descricao, top_k=1)
            if resultados:
                return f"Encontrei na memória: '{resultados[0]}'. Tente tocar isso."
            return "Nada relevante encontrado na memória pessoal."
        except Exception as e:
            logger.error(f"Erro na tool memoria: {e}")
            return "Erro ao consultar memória."