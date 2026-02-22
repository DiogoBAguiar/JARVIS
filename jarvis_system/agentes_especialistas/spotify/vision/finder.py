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
        self.pause_images = [] # Adicionado: Referências de Pause
        
        paths_play = [
            os.path.join(base_dir, "img", "play_spotify.png"),      # Botão Verde Grande (Play)
            os.path.join(base_dir, "img", "play_small_white.png")   # Botão Lista (Play)
        ]
        
        paths_pause = [
            os.path.join(base_dir, "img", "pause_spotify.png")      # Botão Verde Grande (Pause)
        ]
        
        for p in paths_play:
            if os.path.exists(p):
                img = cv2.imread(p)
                if img is not None: self.play_images.append((os.path.basename(p), img))
            else:
                logger.warning(f"Imagem de referência (Play) não encontrada: {p}")
                
        for p in paths_pause:
            if os.path.exists(p):
                img = cv2.imread(p)
                if img is not None: self.pause_images.append((os.path.basename(p), img))
            else:
                logger.warning(f"Imagem de referência (Pause) não encontrada: {p}. Cria para evitar falsos positivos!")

    def procurar_botao_play(self, region=None):
        """
        Busca o botão play redimensionando a referência dinamicamente.
        Valida se o botão encontrado não é na verdade um botão de Pause.
        """
        try:
            bbox = None
            if region:
                x, y, w, h = region
                bbox = (x, y, x + w, y + h)

            screenshot = ImageGrab.grab(bbox=bbox)
            screen_np = np.array(screenshot)
            screen_cv = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
        except Exception as e:
            logger.error(f"Erro ao capturar tela para busca visual: {e}")
            return None

        melhor_play_score = 0.0
        melhor_play_loc = None
        melhor_escala = 1.0
        nome_play = ""

        # --- BUSCA O PLAY ---
        scales = np.linspace(0.5, 1.5, 20)[::-1]
        
        for name, template in self.play_images:
            for scale in scales: 
                new_width = int(template.shape[1] * scale)
                new_height = int(template.shape[0] * scale)
                
                if new_width > screen_cv.shape[1] or new_height > screen_cv.shape[0]:
                    continue

                resized_template = cv2.resize(template, (new_width, new_height))

                try:
                    res = cv2.matchTemplate(screen_cv, resized_template, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

                    if max_val > 0.85 and max_val > melhor_play_score:
                        melhor_play_score = max_val
                        melhor_play_loc = max_loc
                        melhor_escala = scale
                        nome_play = name
                        # Como OpenCV é rápido, pegamos logo o melhor possível e quebramos o loop
                        if max_val > 0.95: break 
                except Exception: continue

        # --- VALIDAÇÃO CONTRA FALSO POSITIVO (PAUSE) ---
        if melhor_play_score > 0.85 and melhor_play_loc:
            # Se a confiança for moderada (85% a 92%), pode ser um Pause disfarçado.
            # Vamos testar o template do Pause no mesmo tamanho da escala que achou o Play.
            if melhor_play_score < 0.94 and self.pause_images:
                melhor_pause_score = 0.0
                for name, template in self.pause_images:
                    new_width = int(template.shape[1] * melhor_escala)
                    new_height = int(template.shape[0] * melhor_escala)
                    
                    if new_width <= screen_cv.shape[1] and new_height <= screen_cv.shape[0]:
                        resized_template = cv2.resize(template, (new_width, new_height))
                        res = cv2.matchTemplate(screen_cv, resized_template, cv2.TM_CCOEFF_NORMED)
                        _, max_val, _, _ = cv2.minMaxLoc(res)
                        if max_val > melhor_pause_score:
                            melhor_pause_score = max_val
                
                # O Grande Duelo de Templates: Qual template se parece mais com o botão que achámos?
                if melhor_pause_score > melhor_play_score:
                    logger.info(f"⚠️ FALSO POSITIVO EVITADO: Achei um botão verde (Score Play: {melhor_play_score:.2f}), mas é o PAUSE (Score Pause: {melhor_pause_score:.2f}). Ignorando.")
                    # Retorna True ou None? Retornar None faz a estratégia tentar o clique cego (Enter).
                    # Retornar True faria a estratégia pensar que o clique foi dado com sucesso.
                    # Mas o finder deve apenas Dizer onde está. Vamos retornar None para fingir que não achou o Play.
                    return "ALREADY_PLAYING"

            # É um Play Genuíno!
            logger.info(f"✅ Botão '{nome_play}' genuíno encontrado! Escala: {melhor_escala:.2f}x | Confiança: {melhor_play_score:.2f}")
            match_x = melhor_play_loc[0] + int(template.shape[1] * melhor_escala) // 2
            match_y = melhor_play_loc[1] + int(template.shape[0] * melhor_escala) // 2

            if region:
                match_x += region[0]
                match_y += region[1]

            return (match_x, match_y)

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