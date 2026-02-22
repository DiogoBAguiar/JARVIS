import logging
import pyautogui
import time
import os
from difflib import SequenceMatcher

try:
    from jarvis_system.cortex_motor.camera.spatial_memory import spatial_mem
except ImportError:
    spatial_mem = None

logger = logging.getLogger("SPOTIFY_FILTER")

class FilterManager:
    """
    Gerencia a barra de filtros do Spotify.
    
    VERSÃO 5.2 (Fuzzy Match Agressivo):
    - Sobrevive ao lixo gerado nas bordas do recorte de imagem (ex: "ts Artistas Ál").
    """

    def __init__(self, vision, window):
        self.vision = vision
        self.window = window

    def selecionar(self, nomes_alvo: list) -> tuple:
        target_str = "/".join(nomes_alvo)
        termo_principal = nomes_alvo[0]
        
        key_primary = f"filter_btn_{termo_principal}"
        key_backup = f"filter_btn_{termo_principal}_alt"

        rect = self.window.obter_geometria()
        if not rect: return None

        win_left, win_top, win_right, win_bottom = rect
        width = win_right - win_left
        height = win_bottom - win_top

        # =========================================================
        # FASE 1: SNIPER DUPLO
        # =========================================================
        if spatial_mem:
            if self._tentar_sniper(width, height, win_left, win_top, key_primary, nomes_alvo, "Principal"):
                return self._recuperar_abs(width, height, win_left, win_top, key_primary)
            if self._tentar_sniper(width, height, win_left, win_top, key_backup, nomes_alvo, "Backup"):
                return self._recuperar_abs(width, height, win_left, win_top, key_backup)

        # =========================================================
        # FASE 2: CANHÃO (Busca Visual c/ Fuzzy Agressivo)
        # =========================================================
        logger.info(f"🧹 [Canhão] Varrendo visualmente para: '{target_str}'...")
        
        sidebar_margin = 150
        top_offset = 60 
        search_height = 60 
        search_width = int(width * 0.7) 
        
        region_top = (
            int(win_left + sidebar_margin), 
            int(win_top + top_offset), 
            int(search_width), 
            int(search_height)
        )

        elementos = self.vision.ler_tela(region=region_top)
        
        melhor_candidato = None
        melhor_score = 0.0
        texto_encontrado = ""

        # Fuzzy Matching Agressivo (Sobrevivência ao Lixo de OCR)
        for bbox, texto, conf in elementos:
            txt_lower = texto.lower().strip()
            # Remove acentos e caracteres estranhos do que o OCR leu
            txt_clean = txt_lower.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
            
            for alvo in nomes_alvo:
                alvo_clean = alvo.lower()
                score = 0.0
                
                # 1. Match Perfeito (Raro com lixo nas bordas)
                if alvo_clean == txt_clean: 
                    score = 1.0
                # 2. Match por Substring Exata (O mais provável de funcionar aqui)
                elif alvo_clean in txt_clean: 
                    score = 0.95
                # 3. Match por Sequência (Caso o OCR erre uma letra)
                else:
                    score = SequenceMatcher(None, txt_clean, alvo_clean).ratio()

                if score > 0.70 and score > melhor_score:
                    melhor_score = score
                    melhor_candidato = bbox
                    texto_encontrado = texto

        if melhor_candidato:
            (tl, tr, br, bl) = melhor_candidato
            cx_box = int((tl[0] + br[0]) / 2)
            cy_box = int((tl[1] + br[1]) / 2)
            
            final_x = cx_box
            final_y = cy_box
            if cx_box < region_top[0]:
                final_x += region_top[0]
                final_y += region_top[1]
            
            logger.info(f"🔘 Filtro '{texto_encontrado}' encontrado ({int(melhor_score*100)}%): Clicando em ({final_x}, {final_y})")
            self._clicar(final_x, final_y)
            
            # Rotação de Memória
            if spatial_mem:
                rel_x = final_x - win_left
                rel_y = final_y - win_top
                coords_old_primary = spatial_mem.buscar_coordenada(width, height, key_primary)
                if coords_old_primary:
                    if abs(coords_old_primary[0] - rel_x) > 20 or abs(coords_old_primary[1] - rel_y) > 20:
                        spatial_mem.memorizar_coordenada(width, height, key_backup, coords_old_primary[0], coords_old_primary[1])

                spatial_mem.memorizar_coordenada(width, height, key_primary, rel_x, rel_y)

            return (final_x, final_y)

        logger.warning(f"❌ Filtro '{target_str}' não encontrado na faixa restrita.")
        return None

    def _tentar_sniper(self, w, h, wl, wt, key, keywords, slot_name):
        coords = spatial_mem.buscar_coordenada(w, h, key)
        if coords:
            abs_x = wl + coords[0]
            abs_y = wt + coords[1]
            
            if self._validar_posicao(abs_x, abs_y, keywords):
                logger.info(f"✅ [Sniper {slot_name}] Validação OK! Clicando.")
                self._clicar(abs_x, abs_y)
                return True
            else:
                logger.warning(f"⚠️ [Sniper {slot_name}] Falhou. Esquecendo memória...")
                if spatial_mem:
                    spatial_mem.esquecer_coordenada(key)
        return False

    def _recuperar_abs(self, w, h, wl, wt, key):
        coords = spatial_mem.buscar_coordenada(w, h, key)
        if coords: return (wl + coords[0], wt + coords[1])
        return None

    def _validar_posicao(self, x, y, keywords):
        w, h = 140, 60 
        left = max(0, x - w//2)
        top = max(0, y - h//2)
        region = (int(left), int(top), int(w), int(h))
        
        try:
            resultado = self.vision.ler_tela(region=region)
            for _, texto, _ in resultado:
                txt_clean = texto.lower().strip().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
                if any(k.lower() in txt_clean for k in keywords):
                    return True
                if any(SequenceMatcher(None, txt_clean, k.lower()).ratio() > 0.8 for k in keywords):
                    return True
            return False
        except: return False

    def _clicar(self, x, y):
        x, y = int(x), int(y)
        pyautogui.moveTo(x, y, duration=0.4)
        pyautogui.click()
        time.sleep(1.0)