import time
import logging
import pyautogui

# Dependências de Baixo Nível
from ..window import WindowManager
from ..input import InputManager
from ..vision import VisionSystem

# Novos Módulos Especialistas (Modularização)
from .process_manager import SpotifyProcessManager
from .visual_navigator import SpotifyVisualNavigator

logger = logging.getLogger("SPOTIFY_CONTROLLER")

class SpotifyController:
    """
    Controlador Principal (Orquestrador).
    Responsabilidade: Coordenar os agentes especialistas.
    """
    
    def __init__(self):
        # 1. Instancia as dependências básicas
        self.window = WindowManager()
        self.input = InputManager() # Agora possui o método robusto .buscar()
        self.vision = VisionSystem()

        # 2. Composição: Injeta dependências nos especialistas
        self.process = SpotifyProcessManager(self.window)
        self.navigator = SpotifyVisualNavigator(self.vision, self.window, self.input)

    def launch_app(self) -> bool:
        """Delega a inicialização para o gerenciador de processos."""
        return self.process.launch()

    def ler_musica_atual(self):
        """Delega a leitura visual para o navegador."""
        return self.navigator.read_current_track()

    def focar_janela(self):
        """Helper para garantir que a janela está ativa."""
        hwnd = self.window.obter_hwnd()
        if hwnd: self.window.focar(hwnd)

    def play_search(self, query: str, tipo: str = "musica"):
        """
        Fluxo Principal: Busca -> Identifica -> Toca.
        CORREÇÃO: Agora aceita 'tipo' para diferenciar Música de Artista.
        """
        # 1. Garante que o App está rodando
        if not self.process.launch():
            return "Falha ao iniciar aplicação."

        try:
            self.focar_janela()

            # 2. Input de Busca (CORREÇÃO: Usa o método novo .buscar)
            # Ele já faz Ctrl+L, Limpa, Digita e dá Enter
            self.input.buscar(query)
            
            logger.info("⏳ Aguardando resultados carregarem...")
            time.sleep(2.0) 

            # 3. Navegação Visual Inteligente (Strategy Pattern)
            # CORREÇÃO: Passamos o 'tipo' e removemos a tentativa manual de clicar no botão verde antes.
            # O navigator decide qual estratégia usar (TrackStrategy ou ArtistStrategy).
            if self.navigator.find_and_click(query, tipo=tipo):
                return f"Tocando {tipo}: {query}"

            # 4. Fallback: Modo Cego (Se as estratégias falharem)
            logger.warning("⌨️ Falha visual total. Acionando modo cego.")
            self._fallback_teclado()
            return "Tentativa via atalhos de teclado (fallback)."

        except Exception as e:
            logger.error(f"Erro no fluxo de reprodução: {e}")
            return f"Erro: {str(e)}"

    def _fallback_teclado(self):
        """Método auxiliar privado para o fallback cego."""
        pyautogui.press('tab')
        time.sleep(0.1)
        pyautogui.press('enter')

    # --- Proxy Methods ---
    # Mantém a interface pública simples para quem chama o Controller
    def resume(self): self.input.midia("play_pause")
    def pause(self): self.input.midia("play_pause")
    def next_track(self): self.input.midia("next")
    def previous_track(self): self.input.midia("prev")
    def scroll(self, direction): self.input.rolar_tela(direction)
    def curtir_musica(self): self.input.midia("like")