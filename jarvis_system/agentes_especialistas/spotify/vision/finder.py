import os
import logging
import pyautogui
from .dependencies import fuzz, DEPENDENCIES_OK

logger = logging.getLogger("VISION_FINDER")

class VisualFinder:
    """Especialista em encontrar elementos na tela."""

    def __init__(self, ocr_processor):
        self.ocr = ocr_processor
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Agora carregamos uma LISTA de alvos possíveis
        self.play_images = [
            os.path.join(base_dir, "img", "play_spotify.png"),      # Botão Verde Grande
            os.path.join(base_dir, "img", "play_small_white.png")   # Botão Lista (NOVO)
        ]

    def procurar_botao_play(self, region=None):
        """Busca qualquer uma das variações do botão play."""
        
        for img_path in self.play_images:
            if not os.path.exists(img_path):
                continue # Pula se a imagem não existir

            try:
                # Tenta achar essa versão do botão
                pos = pyautogui.locateOnScreen(
                    img_path, 
                    confidence=0.8, 
                    grayscale=False, 
                    region=region
                )
                if pos:
                    logger.info(f"✅ Botão encontrado usando referência: {os.path.basename(img_path)}")
                    return pos
            except pyautogui.ImageNotFoundException:
                continue
            except Exception as e:
                logger.error(f"Erro na busca visual: {e}")
        
        return None # Nenhum dos botões foi encontrado

    def encontrar_texto_fuzzy(self, texto_alvo: str, region=None, min_score=80):
        # ... (O resto do código fuzzy continua igual) ...
        # (Copie o método encontrar_texto_fuzzy do seu código anterior)
        if not DEPENDENCIES_OK: return None

        leituras = self.ocr.ler_tela(region)
        if not leituras: return None

        texto_alvo = texto_alvo.lower()
        melhor_bbox = None
        maior_score = 0

        for (bbox, texto_lido, _) in leituras:
            texto_lido_lower = texto_lido.lower()
            score_parcial = fuzz.partial_ratio(texto_alvo, texto_lido_lower)
            score_ratio = fuzz.ratio(texto_alvo, texto_lido_lower)
            score_final = max(score_parcial, score_ratio)

            if score_final > maior_score and score_final >= min_score:
                maior_score = score_final
                melhor_bbox = bbox

        if melhor_bbox:
            logger.info(f"🎯 Alvo encontrado: '{texto_alvo}' (Score: {maior_score}%)")
            (tl, tr, br, bl) = melhor_bbox
            center_x = int((tl[0] + br[0]) / 2)
            center_y = int((tl[1] + br[1]) / 2)
            return (center_x, center_y)
        
        return None