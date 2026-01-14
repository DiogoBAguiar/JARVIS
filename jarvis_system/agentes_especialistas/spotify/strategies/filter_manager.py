import logging
import pyautogui
import time
from difflib import SequenceMatcher

logger = logging.getLogger("SPOTIFY_FILTER")

class FilterManager:
    """
    Gerencia a barra de filtros do Spotify (Tudo, Músicas, Artistas, Podcasts, etc.).
    Centraliza a lógica de OCR e Geometria da barra superior.
    """

    def __init__(self, vision, window):
        self.vision = vision
        self.window = window

    def selecionar(self, nomes_alvo: list) -> tuple:
        """
        Busca um botão na barra de filtros que corresponda a um dos nomes na lista.
        Ex: nomes_alvo = ["música", "musica", "songs"]
        
        Retorna: (x, y) do clique ou None se falhar.
        """
        target_str = "/".join(nomes_alvo)
        logger.info(f"🧹 Buscando filtro: '{target_str}'...")

        # 1. Define a região da barra de filtros (Baseado na lógica do seu artist.py)
        rect = self.window.obter_geometria()
        if not rect:
            logger.error("❌ Não foi possível obter geometria da janela.")
            return None

        win_left, win_top, win_right, _ = rect
        width = win_right - win_left
        
        # Ignora sidebar (300px) e foca no topo
        sidebar_margin = 300
        search_width = width - sidebar_margin
        
        # Altura de 300px do topo deve ser suficiente para pegar os chips de filtro
        region_top = (win_left + sidebar_margin, win_top, search_width, 300)

        # 2. Leitura OCR
        elementos = self.vision.ler_tela(region=region_top)
        
        melhor_candidato = None
        melhor_score = 0.0

        # 3. Fuzzy Matching para encontrar o botão
        for bbox, texto, conf in elementos:
            txt_lower = texto.lower()
            
            for alvo in nomes_alvo:
                # Compara similaridade (ajuda com erros de OCR como 'MUsicas')
                score = SequenceMatcher(None, txt_lower, alvo.lower()).ratio()
                
                # Se for match exato ou muito alto
                if alvo.lower() in txt_lower: score = 1.0

                if score > 0.8 and score > melhor_score:
                    melhor_score = score
                    melhor_candidato = bbox
                    logger.debug(f"   Candidato: '{texto}' ({score:.2f})")

        # 4. Clicar
        if melhor_candidato:
            (tl, tr, br, bl) = melhor_candidato
            cx = int((tl[0] + br[0]) / 2)
            cy = int((tl[1] + br[1]) / 2)
            
            logger.info(f"🔘 Filtro encontrado ({int(melhor_score*100)}%): Clicando em ({cx}, {cy})")
            
            pyautogui.moveTo(cx, cy, duration=0.4)
            pyautogui.click()
            time.sleep(1.5) # Tempo para a lista carregar
            return (cx, cy)

        logger.warning(f"❌ Filtro '{target_str}' não encontrado visualmente.")
        return None