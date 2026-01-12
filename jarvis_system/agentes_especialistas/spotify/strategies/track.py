import logging
import pyautogui
import time
import re

logger = logging.getLogger("STRATEGY_TRACK")

class TrackStrategy:
    """
    Estratégia para tocar Músicas Específicas (Tracks).
    Fluxo: Filtro 'Músicas' -> Clique Cego no 1º Item -> Validação.
    """

    def __init__(self, vision, window):
        self.vision = vision
        self.window = window

    def executar(self, termo_busca):
        logger.info(f"🎹 [Estratégia] Iniciando modo Faixa para: '{termo_busca}'")
        
        # 1. Filtro
        coords_filtro = self._ativar_filtro_musicas()
        pyautogui.moveRel(0, 200) # Limpa visão
        
        # 2. Clique Turbo (Baseado na âncora do filtro)
        if coords_filtro:
            btn_x, btn_y = coords_filtro
            # A 1ª música fica exatos 100px abaixo do botão de filtro
            target_x = btn_x 
            
            # Ajuste horizontal seguro: Centraliza na lista
            rect = self.window.obter_geometria()
            if rect: target_x = rect[0] + 450 

            target_y = btn_y + 100
            
            logger.info(f"⚡ CLICK TURBO (Relativo): ({target_x}, {target_y})")
            if self._clicar_e_validar(target_x, target_y, termo_busca):
                return True

        # 3. Fallback Geométrico (Se não achou botão)
        rect = self.window.obter_geometria()
        if rect:
            win_left, win_top, _, _ = rect
            # Heurística: Topo da janela + 220px
            target_x = win_left + 450
            target_y = win_top + 220
            
            logger.info(f"⚡ CLICK TURBO (Absoluto): ({target_x}, {target_y})")
            if self._clicar_e_validar(target_x, target_y, termo_busca):
                return True

        logger.warning("❌ Estratégia de Faixa falhou.")
        return False

    def _ativar_filtro_musicas(self):
        logger.info("🧹 Procurando filtro 'Músicas'...")
        rect = self.window.obter_geometria()
        if not rect: return None
        
        win_left, win_top, win_right, _ = rect
        width = win_right - win_left
        region_top = (win_left, win_top, width, 300)

        elementos = self.vision.ler_tela(region=region_top)
        
        for bbox, texto, _ in elementos:
            txt = texto.lower()
            if "música" in txt or "musica" in txt or "song" in txt:
                (tl, tr, br, bl) = bbox
                cx = int((tl[0] + br[0]) / 2)
                cy = int((tl[1] + br[1]) / 2)
                logger.info(f"🔘 Filtro encontrado em ({cx}, {cy}). Clicando...")
                pyautogui.moveTo(cx, cy, duration=0.3)
                pyautogui.click()
                time.sleep(1.5) 
                return (cx, cy)
        return None

    def _clicar_e_validar(self, x, y, termo):
        self._clique_duplo_manual(x, y)
        return self._validar_mudanca(termo)

    def _clique_duplo_manual(self, x, y):
        pyautogui.moveTo(x, y, duration=0.3)
        time.sleep(0.05)
        pyautogui.click()
        time.sleep(0.05)
        pyautogui.click()
        pyautogui.moveRel(200, 0)

    def _validar_mudanca(self, texto_alvo, tentativas=3):
        logger.info("⏳ Validando...")
        alvo_tokens = texto_alvo.lower().split()
        for _ in range(tentativas):
            # Pequena duplicação do read_current_track para isolamento (ou passamos via callback)
            # Para simplificar aqui, vou fazer uma leitura rápida local
            tocando = self._ler_player_rapido()
            if tocando:
                if any(t in tocando for t in alvo_tokens if len(t) > 3):
                    logger.info(f"🎧 Tocando: {tocando}")
                    return True
            time.sleep(1.0)
        return False

    def _ler_player_rapido(self):
        """Leitura simplificada do player apenas para validação interna."""
        rect = self.window.obter_geometria()
        if not rect: return None
        wl, wt, wr, wb = rect
        
        # Ajuste de coordenadas
        reg_l = wl + 20
        reg_t = max(0, wb - 130)
        
        # Proteção de borda
        sw, sh = pyautogui.size()
        if reg_l + 350 > sw: reg_l = sw - 350
        
        region = (reg_l, reg_t, 350, 100)
        
        try:
            res = self.vision.ler_tela(region=region)
            txts = [t for _, t, c in res if len(t) > 2 and c > 0.4 and not re.search(r'\d+:\d+', t)]
            return " ".join(txts).lower()
        except: return None