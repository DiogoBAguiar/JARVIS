import logging
import pyautogui
import re
from ..strategies.track import TrackStrategy
from ..strategies.artist import ArtistStrategy # <--- Importa a nova estratégia

logger = logging.getLogger("SPOTIFY_NAVIGATOR")

class SpotifyVisualNavigator:
    """
    Navegador Visual (Gerente).
    Delega a execução para estratégias especializadas.
    """
    
    def __init__(self, vision_system, window_manager, input_manager):
        self.vision = vision_system
        self.window = window_manager
        self.input = input_manager
        
        # Inicializa as Estratégias
        self.track_strategy = TrackStrategy(vision_system, window_manager)
        self.artist_strategy = ArtistStrategy(vision_system, window_manager) # <--- Instancia

    def read_current_track(self):
        # ... (Mantenha o método read_current_track igual ao anterior) ...
        # (Vou omitir aqui para economizar espaço, mas mantenha ele!)
        try:
            rect = self.window.obter_geometria()
            if not rect: return None
            win_left, win_top, win_right, win_bottom = rect
            region_left = win_left + 20
            region_top = win_bottom - 130 
            if region_top < 0: region_top = 0
            screen_w, screen_h = pyautogui.size()
            if region_left + 350 > screen_w: region_left = screen_w - 350
            region_player = (region_left, region_top, 350, 100)
            resultados = self.vision.ler_tela(region=region_player)
            textos_limpos = []
            for (_, txt, conf) in resultados:
                if len(txt) > 2 and conf > 0.4 and not re.search(r'\d+:\d+', txt):
                    textos_limpos.append(txt)
            if textos_limpos: return {"raw": " ".join(textos_limpos)}
            return None
        except: return None

    def find_and_click(self, text_target: str, tipo="musica"):
        """
        Roteador de Estratégias.
        Args:
            text_target: O que buscar.
            tipo: 'musica' (padrão) ou 'artista'.
        """
        if tipo == "artista":
            logger.info(f"🔀 Delegando busca de '{text_target}' para Strategy: ARTIST")
            return self.artist_strategy.executar(text_target)
        
        else:
            # Padrão: Música
            logger.info(f"🔀 Delegando busca de '{text_target}' para Strategy: TRACK")
            return self.track_strategy.executar(text_target)

    def click_green_play_button(self):
        try:
            pos = self.vision.procurar_botao_play()
            if pos: pyautogui.click(pyautogui.center(pos)); return True
        except: return False
        return False