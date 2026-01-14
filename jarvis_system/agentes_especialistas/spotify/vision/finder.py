import os
import logging
import cv2
import numpy as np
import pyautogui
from PIL import ImageGrab
from .dependencies import fuzz, DEPENDENCIES_OK

logger = logging.getLogger("VISION_FINDER")

class VisualFinder:
    """
    Especialista em encontrar elementos na tela usando Visão Computacional Avançada.
    Implementa Multi-Scale Template Matching para achar botões de qualquer tamanho
    e evitar erros de dimensão.
    """

    def __init__(self, ocr_processor):
        self.ocr = ocr_processor
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Carrega as imagens de referência na memória para performance
        self.play_images = []
        paths = [
            os.path.join(base_dir, "img", "play_spotify.png"),      # Botão Verde Grande
            os.path.join(base_dir, "img", "play_small_white.png")   # Botão Lista
        ]
        
        for p in paths:
            if os.path.exists(p):
                # Carrega em formato que o OpenCV entende (BGR)
                img = cv2.imread(p)
                if img is not None:
                    self.play_images.append((os.path.basename(p), img))
                else:
                    logger.warning(f"Falha ao carregar imagem (formato inválido?): {p}")
            else:
                 logger.warning(f"Imagem de referência não encontrada: {p}")

    def procurar_botao_play(self, region=None):
        """
        Busca o botão play redimensionando a referência dinamicamente.
        Isso permite achar o botão seja ele gigante ou pequeno,
        e previne erros de 'needle dimension > haystack'.
        """
        
        # 1. Tira um print da região (ou tela toda)
        try:
            # Ajuste de bbox para PIL (Left, Top, Right, Bottom) vs (X, Y, W, H)
            bbox = None
            if region:
                x, y, w, h = region
                bbox = (x, y, x + w, y + h)

            screenshot = ImageGrab.grab(bbox=bbox)
            # Converte PIL (RGB) para OpenCV (BGR)
            screen_np = np.array(screenshot)
            screen_cv = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
        except Exception as e:
            logger.error(f"Erro ao capturar tela para busca visual: {e}")
            return None

        # 2. Itera sobre as imagens de referência (Verde e Branco)
        for name, template in self.play_images:
            
            # 3. MÁGICA DA MULTI-ESCALA:
            # Tenta 20 tamanhos diferentes: de 50% (0.5) até 150% (1.5) do original
            # [::-1] inverte para começar tentando os tamanhos maiores primeiro
            scales = np.linspace(0.5, 1.5, 20)[::-1]
            
            for scale in scales: 
                # Redimensiona o template (referência)
                new_width = int(template.shape[1] * scale)
                new_height = int(template.shape[0] * scale)
                
                # Proteção Crítica: Se o template redimensionado for maior que a tela de busca,
                # pula essa escala. Isso evita o crash do OpenCV.
                if new_width > screen_cv.shape[1] or new_height > screen_cv.shape[0]:
                    continue

                resized_template = cv2.resize(template, (new_width, new_height))

                # Tenta o match
                try:
                    res = cv2.matchTemplate(screen_cv, resized_template, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

                    # Se a confiança for alta (> 0.85)
                    if max_val > 0.85:
                        logger.info(f"✅ Botão '{name}' encontrado! Escala: {scale:.2f}x | Confiança: {max_val:.2f}")
                        
                        # Calcula o centro do botão encontrado NA IMAGEM CAPTURADA
                        match_x = max_loc[0] + new_width // 2
                        match_y = max_loc[1] + new_height // 2

                        # Se usamos uma região (crop), precisamos somar o offset para ter a coord absoluta da tela
                        if region:
                            match_x += region[0]
                            match_y += region[1]

                        return (match_x, match_y)
                except Exception:
                    continue

        return None

    def encontrar_texto_fuzzy(self, texto_alvo: str, region=None, min_score=80):
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