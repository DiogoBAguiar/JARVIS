import logging
import pyautogui
import re

# Importação da Memória Espacial (Otimização de Performance)
try:
    from jarvis_system.cortex_motor.camera.spatial_memory import spatial_mem
except ImportError:
    spatial_mem = None # Fallback se não estiver configurado

from ..strategies.track import TrackStrategy
from ..strategies.artist import ArtistStrategy
from ..strategies.filter_manager import FilterManager

logger = logging.getLogger("SPOTIFY_NAVIGATOR")

class SpotifyVisualNavigator:
    """
    Navegador Visual (Gerente).
    Coordena o FilterManager para selecionar a aba correta e 
    delega a interação específica para estratégias (Track/Artist).
    
    ATUALIZAÇÃO V3.7: Integração com Memória Espacial (Cache de UI).
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
        Roteador Inteligente com CACHE:
        1. Verifica Memória Espacial para clicar no filtro instantaneamente.
        2. Se falhar, usa Visão (OCR) e memoriza a posição.
        3. Executa a estratégia de conteúdo.
        """
        tipo = tipo.lower()
        logger.info(f"🔀 Navegando para: '{text_target}' | Tipo: {tipo}")

        # Obter geometria da janela para usar como chave do cache
        rect = self.window.obter_geometria() # (x, y, x2, y2)
        win_w, win_h = 0, 0
        if rect:
            win_w = rect[2] - rect[0]
            win_h = rect[3] - rect[1]

        # --- PASSO 1: FILTRAGEM VISUAL (COM CACHE) ---
        palavras_chave = self.mapa_filtros.get(tipo)
        coords_filtro = None
        usou_cache = False

        if palavras_chave:
            nome_filtro_cache = f"filter_btn_{tipo}"
            
            # A) Tenta Via Rápida (Memória Espacial)
            if spatial_mem and rect:
                rel_coords = spatial_mem.buscar_coordenada(win_w, win_h, nome_filtro_cache)
                if rel_coords:
                    abs_x = rect[0] + rel_coords[0]
                    abs_y = rect[1] + rel_coords[1]
                    logger.info(f"⚡ [Cache UI] Clicando no filtro '{tipo}' em ({abs_x}, {abs_y})")
                    pyautogui.click(abs_x, abs_y)
                    coords_filtro = (abs_x, abs_y)
                    usou_cache = True
            
            # B) Via Lenta (OCR) - Se não tinha cache ou falhou
            if not coords_filtro:
                logger.info(f"👁️ [OCR] Buscando filtro visualmente...")
                coords_filtro = self.filter_manager.selecionar(palavras_chave)
                
                # Aprende para a próxima vez
                if coords_filtro and spatial_mem and rect:
                    rel_x = coords_filtro[0] - rect[0]
                    rel_y = coords_filtro[1] - rect[1]
                    spatial_mem.memorizar_coordenada(win_w, win_h, nome_filtro_cache, rel_x, rel_y)

            if not coords_filtro:
                logger.warning(f"⚠️ Filtro para '{tipo}' falhou. Tentando busca genérica.")
        else:
            logger.warning(f"Tipo '{tipo}' não mapeado. Ignorando filtros.")

        # --- PASSO 2: EXECUÇÃO DA ESTRATÉGIA ---
        
        if tipo in ["artista", "artist", "album", "playlist"]:
            logger.info(f"🎨 Executando Strategy: ARTIST")
            # Se usou cache, damos um pequeno sleep para garantir que a UI atualizou
            if usou_cache: pyautogui.sleep(0.5) 
            return self.artist_strategy.executar(text_target, anchor_point=coords_filtro)
        
        else:
            # Padrão: Música (Track)
            logger.info(f"🎹 Executando Strategy: TRACK")
            if usou_cache: pyautogui.sleep(0.5)
            return self.track_strategy.executar(text_target, anchor_point=coords_filtro)

    def click_green_play_button(self):
        try:
            pos = self.vision.procurar_botao_play()
            if pos: 
                pyautogui.click(pyautogui.center(pos))
                return True
        except: return False
        return False