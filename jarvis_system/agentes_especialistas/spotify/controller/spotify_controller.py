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

# --- Importa o Driver Web (Controle Remoto) ---
try:
    from ..drivers.web_driver import SpotifyWebDriver
except ImportError:
    SpotifyWebDriver = None
    print("⚠️ Aviso: SpotifyWebDriver não encontrado. O modo rápido será desativado.")

logger = logging.getLogger("SPOTIFY_CONTROLLER")

class SpotifyController:
    """
    Controlador Principal (Orquestrador).
    Responsabilidade: Coordenar os agentes especialistas (Web e Visual).
    Estratégia: Tenta via Web (Rápido) -> Se falhar, usa Visual (Robusto).
    """
    
    def __init__(self):
        # 1. Instancia as dependências básicas
        self.window = WindowManager()
        self.input = InputManager() 
        self.vision = VisionSystem()

        # 2. Composição: Injeta dependências nos especialistas Visuais
        self.process = SpotifyProcessManager(self.window)
        self.navigator = SpotifyVisualNavigator(self.vision, self.window, self.input)

        # 3. Inicializa o Driver Web (Modo Fantasma/Rápido)
        # headless=True para rodar invisível (mais rápido).
        if SpotifyWebDriver:
            self.web_driver = SpotifyWebDriver(headless=False)
        else:
            self.web_driver = None

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
        Fluxo Principal: Web Driver (Tentativa A) -> Visual Desktop (Tentativa B).
        """
        
        # --- TENTATIVA 1: WEB DRIVER (Velocidade & Controle Remoto) ---
        if self.web_driver:
            logger.info(f"⚡ [Controller] Tentando via Web Driver: '{query}' (Tipo: {tipo})")
            try:
                # MUDANÇA CRÍTICA: Passamos None para ativar o Scanner Automático do Driver
                # O Driver vai descobrir sozinho que o nome do PC é "Jarvas"
                sucesso = self.web_driver.tocar(query, tipo=tipo, device_name=None)
                
                if sucesso:
                    return f"Tocando via Web (Remote): {query}"
                else:
                    logger.warning("⚠️ [Controller] Web Driver retornou False. Iniciando Fallback...")
            
            except Exception as e:
                logger.warning(f"⚠️ [Controller] Web Driver falhou: {e}. Iniciando Fallback...")
        
        # --- TENTATIVA 2: VISUAL DESKTOP (Backup Robusto) ---
        logger.info("👁️ [Controller] Ativando Modo Visual (Força Bruta)...")

        # 1. Garante que o App está rodando
        if not self.process.launch():
            return "Falha ao iniciar aplicação Desktop."

        try:
            self.focar_janela()

            # 2. Input de Busca
            self.input.buscar(query)
            
            logger.info("⏳ Aguardando resultados carregarem...")
            time.sleep(2.0) 

            # 3. Navegação Visual Inteligente
            if self.navigator.find_and_click(query, tipo=tipo):
                return f"Tocando {tipo} (Visual): {query}"

            # 4. Fallback: Modo Cego
            logger.warning("⌨️ Falha visual total. Acionando modo cego.")
            self._fallback_teclado()
            return "Tentativa via atalhos de teclado (fallback)."

        except Exception as e:
            logger.error(f"Erro no fluxo de reprodução Visual: {e}")
            return f"Erro: {str(e)}"

    def _fallback_teclado(self):
        """Método auxiliar privado para o fallback cego."""
        pyautogui.press('tab')
        time.sleep(0.1)
        pyautogui.press('enter')

    # --- Proxy Methods ---
    def resume(self): self.input.midia("play_pause")
    def pause(self): self.input.midia("play_pause")
    def next_track(self): self.input.midia("next")
    def previous_track(self): self.input.midia("prev")
    def scroll(self, direction): self.input.rolar_tela(direction)
    def curtir_musica(self): self.input.midia("like")