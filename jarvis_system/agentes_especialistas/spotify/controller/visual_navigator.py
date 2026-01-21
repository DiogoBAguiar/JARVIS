import logging
import pyautogui
import re

# NOTA: O Navigator não acessa mais o cache diretamente. 
# Quem cuida da "Memória de Filtros" é o FilterManager.

from ..strategies.track import TrackStrategy
from ..strategies.artist import ArtistStrategy
from ..strategies.filter_manager import FilterManager

logger = logging.getLogger("SPOTIFY_NAVIGATOR")

class SpotifyVisualNavigator:
    """
    Navegador Visual (Gerente).
    Coordena o FilterManager para selecionar a aba correta e 
    delega a interação específica para estratégias (Track/Artist).
    
    ATUALIZAÇÃO V4.0: Delegação Total de Cache para FilterManager.
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
            
            # Variações de Artista
            "artist": ["artista", "artists", "artistas"],
            "artista": ["artista", "artists", "artistas"],
            "artistas": ["artista", "artists", "artistas"],
            "musica/artistas": ["artista", "artists", "artistas"],
            
            "album": ["álbuns", "albuns", "albums"],
            
            # Variações de Playlist
            "playlist": ["playlists", "playlist"],
            "playlists": ["playlists", "playlist"],
            
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
        Fluxo Otimizado:
        1. Identifica a chave correta do filtro (normalização).
        2. Pede ao FilterManager para garantir a aba (usando Cache+Sniper ou OCR).
        3. Executa a estratégia de conteúdo.
        """
        tipo_original = tipo.lower()
        
        # --- NORMALIZAÇÃO DE TIPO ---
        if "artista" in tipo_original: tipo_chave = "artista"
        elif "playlist" in tipo_original: tipo_chave = "playlist"
        elif "album" in tipo_original: tipo_chave = "album"
        else: tipo_chave = "musica"

        logger.info(f"🔀 Navegando para: '{text_target}' | Tipo: {tipo_chave}")

        # --- PASSO 1: FILTRAGEM VISUAL ---
        # Busca palavras chave usando o tipo original ou a chave normalizada
        palavras_chave = self.mapa_filtros.get(tipo_original) or self.mapa_filtros.get(tipo_chave)
        coords_filtro = None

        if palavras_chave:
            # O FilterManager agora cuida de tudo: Cache, Validação Visual e OCR
            # Se ele retornar algo, significa que clicou com sucesso (rápido ou lento)
            coords_filtro = self.filter_manager.selecionar(palavras_chave)
            
            if not coords_filtro:
                logger.warning(f"⚠️ Filtro para '{tipo_chave}' falhou ou não foi encontrado.")
        else:
            logger.warning(f"Tipo '{tipo_original}' não mapeado. Ignorando filtros.")

        # --- PASSO 2: EXECUÇÃO DA ESTRATÉGIA ---
        
        if tipo_chave in ["artista", "album", "playlist"]:
            logger.info(f"🎨 Executando Strategy: ARTIST")
            # Pequeno delay para garantir transição de tela após clique no filtro
            if coords_filtro: pyautogui.sleep(0.8)
            return self.artist_strategy.executar(text_target, anchor_point=coords_filtro)
        
        else:
            # Padrão: Música (Track)
            logger.info(f"🎹 Executando Strategy: TRACK")
            if coords_filtro: pyautogui.sleep(0.5)
            return self.track_strategy.executar(text_target, anchor_point=coords_filtro)

    def click_green_play_button(self):
        try:
            pos = self.vision.procurar_botao_play()
            if pos: 
                pyautogui.click(pyautogui.center(pos))
                return True
        except: return False
        return False