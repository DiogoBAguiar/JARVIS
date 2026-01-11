import logging
import time
import pyautogui
try:
    import win32gui
except ImportError:
    win32gui = None

# Dependências de Infraestrutura (note o .. para subir um nível da pasta controller)
from ..vision import VisionSystem
from ..window import WindowManager
from ..input import InputManager

logger = logging.getLogger("SPOTIFY_VISUAL")

class SpotifyVisualNavigator:
    """Responsável por localizar elementos na tela e interagir visualmente."""
    
    def __init__(self, vision: VisionSystem, window: WindowManager, input_manager: InputManager):
        self.vision = vision
        self.window = window
        self.input = input_manager

    def _get_window_region(self, hwnd):
        if not win32gui: return None
        try:
            rect = win32gui.GetWindowRect(hwnd)
            w, h = rect[2] - rect[0], rect[3] - rect[1]
            return (rect[0], rect[1], w, h)
        except: return None

    def _get_player_region(self, hwnd):
        """Calcula a região do player (canto inferior esquerdo)."""
        if not win32gui: return None
        try:
            rect = win32gui.GetWindowRect(hwnd)
            w, h = rect[2] - rect[0], rect[3] - rect[1]
            # 15% altura, 30% largura
            return (rect[0], rect[1] + h - int(h*0.15), int(w*0.30), int(h*0.15))
        except: return None

    def _click_at(self, hwnd, x_global, y_global):
        """Abstração de clique seguro (Global -> Local)."""
        if win32gui:
            try:
                pl = win32gui.ScreenToClient(hwnd, (int(x_global), int(y_global)))
                self.input.clique_fantasma_com_enter(hwnd, pl[0], pl[1])
                return True
            except Exception as e:
                logger.error(f"Erro ao clicar: {e}")
        
        # Fallback PyAutoGUI
        pyautogui.click(x_global, y_global)
        return True

    def read_current_track(self):
        """Lê a música atual usando OCR na região do player."""
        hwnd = self.window.obter_hwnd()
        if not hwnd: return None
        
        region = self._get_player_region(hwnd)
        if not region: return None
        
        logger.info("👀 Lendo metadados da faixa...")
        readings = self.vision.ler_tela(region=region)
        
        valid_texts = [t[1] for t in readings if len(t[1]) > 2]
        if not valid_texts: return None
        
        return {
            "titulo": valid_texts[0],
            "artista": valid_texts[1] if len(valid_texts) > 1 else "Desconhecido",
            "raw": " - ".join(valid_texts)
        }

    def click_green_play_button(self) -> bool:
        """Tenta localizar e clicar no botão 'Play' verde."""
        hwnd = self.window.obter_hwnd()
        if not hwnd: return False
        
        region = self._get_window_region(hwnd)
        
        # Usa o VisionSystem para achar a imagem
        botao = self.vision.procurar_botao_play(region=region)
        
        if botao:
            centro = pyautogui.center(botao)
            logger.info("🟢 Botão Visual encontrado. Clicando...")
            self._click_at(hwnd, centro.x, centro.y)
            return True
            
        return False

    def find_and_click(self, text_target: str, attempts: int = 3) -> bool:
        """Busca fuzzy de texto e clica."""
        hwnd = self.window.obter_hwnd()
        if not hwnd: return False
        
        region = self._get_window_region(hwnd)

        for i in range(attempts):
            coords = self.vision.encontrar_texto_fuzzy(text_target, region=region)
            if coords:
                cx, cy = coords
                self._click_at(hwnd, cx, cy)
                return True
                
            if i < attempts - 1:
                self.input.rolar_tela("down", 1)
                time.sleep(0.5)
                # Recalcula região caso janela tenha movido
                region = self._get_window_region(hwnd)
        return False