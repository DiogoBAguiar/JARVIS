import logging
import pyautogui
import re
from ..strategies.track import TrackStrategy
from ..strategies.artist import ArtistStrategy
from ..strategies.filter_manager import FilterManager # <--- Nova Importação

logger = logging.getLogger("SPOTIFY_NAVIGATOR")

class SpotifyVisualNavigator:
    """
    Navegador Visual (Gerente).
    Coordena o FilterManager para selecionar a aba correta e 
    delega a interação específica para estratégias (Track/Artist).
    """
    
    def __init__(self, vision_system, window_manager, input_manager):
        self.vision = vision_system
        self.window = window_manager
        self.input = input_manager
        
        # 1. Inicializa o Gerenciador de Filtros (Cérebro da Barra Superior)
        self.filter_manager = FilterManager(vision_system, window_manager)

        # 2. Inicializa as Estratégias (Injetando o filter_manager)
        self.track_strategy = TrackStrategy(vision_system, window_manager, self.filter_manager)
        self.artist_strategy = ArtistStrategy(vision_system, window_manager, self.filter_manager)
        
        # 3. Mapa de Sinônimos para Filtros
        self.mapa_filtros = {
            "track": ["música", "musica", "songs", "tracks"],
            "musica": ["música", "musica", "songs"],
            
            "artist": ["artista", "artists", "artistas"],
            "artista": ["artista", "artists", "artistas"],
            
            "album": ["álbuns", "albuns", "albums"],
            "playlist": ["playlists", "playlist"],
            "podcast": ["podcasts", "programas"]
        }

    def read_current_track(self):
        """Lê o que está tocando agora na barra inferior."""
        try:
            rect = self.window.obter_geometria()
            if not rect: return None
            win_left, win_top, win_right, win_bottom = rect
            
            # Define região do player (canto inferior esquerdo)
            region_left = win_left + 20
            region_top = win_bottom - 130 
            if region_top < 0: region_top = 0
            
            screen_w, screen_h = pyautogui.size()
            if region_left + 350 > screen_w: region_left = screen_w - 350
            
            region_player = (region_left, region_top, 350, 100)
            
            # Leitura OCR
            resultados = self.vision.ler_tela(region=region_player)
            textos_limpos = []
            for (_, txt, conf) in resultados:
                # Filtra lixo e timestamps (ex: 02:30)
                if len(txt) > 2 and conf > 0.4 and not re.search(r'\d+:\d+', txt):
                    textos_limpos.append(txt)
            
            if textos_limpos: return {"raw": " ".join(textos_limpos)}
            return None
        except: return None

    def find_and_click(self, text_target: str, tipo="musica"):
        """
        Roteador Inteligente:
        1. Seleciona o filtro correto na UI (usando FilterManager).
        2. Passa a localização do filtro como 'âncora' para a estratégia.
        """
        tipo = tipo.lower()
        logger.info(f"🔀 Navegando para: '{text_target}' | Tipo: {tipo}")

        # --- PASSO 1: FILTRAGEM VISUAL ---
        palavras_chave = self.mapa_filtros.get(tipo)
        coords_filtro = None

        if palavras_chave:
            # Tenta clicar no filtro correspondente (Ex: "Artistas")
            coords_filtro = self.filter_manager.selecionar(palavras_chave)
            if not coords_filtro:
                logger.warning(f"⚠️ Filtro para '{tipo}' falhou ou não existe. Tentando busca genérica.")
        else:
            logger.warning(f"Tipo '{tipo}' não mapeado. Ignorando filtros.")

        # --- PASSO 2: EXECUÇÃO DA ESTRATÉGIA ---
        # Se for album/playlist, usamos a estratégia de artista (card grande) como fallback
        if tipo in ["artista", "artist", "album", "playlist"]:
            logger.info(f"🎨 Executando Strategy: ARTIST (Com âncora: {coords_filtro})")
            return self.artist_strategy.executar(text_target, anchor_point=coords_filtro)
        
        else:
            # Padrão: Música (Track)
            logger.info(f"🎹 Executando Strategy: TRACK (Com âncora: {coords_filtro})")
            return self.track_strategy.executar(text_target, anchor_point=coords_filtro)

    def click_green_play_button(self):
        try:
            pos = self.vision.procurar_botao_play()
            if pos: 
                pyautogui.click(pyautogui.center(pos))
                return True
        except: return False
        return False