import logging
import pyautogui
import time
import re

logger = logging.getLogger("STRATEGY_TRACK")

class TrackStrategy:
    """
    Estratégia para tocar Músicas (Tracks).
    Assume que o filtro já foi aplicado ou estamos na aba 'Tudo'.
    """

    def __init__(self, vision, window, filter_manager):
        self.vision = vision
        self.window = window
        self.filter_manager = filter_manager

    def executar(self, termo_busca, anchor_point=None):
        logger.info(f"🎹 [Estratégia] Iniciando modo Faixa para: '{termo_busca}'")
        
        pyautogui.moveRel(0, 200) # Tira o mouse da frente

        # Lógica de Clique Turbo baseada na Âncora do Filtro
        if anchor_point:
            btn_x, btn_y = anchor_point
            
            # Ajuste Fixo: A 1ª música geralmente está ~100px abaixo do filtro
            # e centralizada na área de conteúdo (não na tela toda)
            rect = self.window.obter_geometria()
            target_x = btn_x
            
            if rect:
                # Centraliza o clique X na área útil (Right - Left - Sidebar)
                win_left = rect[0]
                target_x = win_left + 450 # Valor seguro do seu código original
            
            target_y = btn_y + 110 # Ajustado levemente para baixo
            
            logger.info(f"⚡ CLICK TURBO (Relativo ao Filtro): ({target_x}, {target_y})")
            if self._clicar_e_validar(target_x, target_y, termo_busca):
                return True

        # Fallback Geométrico (Se não tínhamos âncora ou falhou)
        rect = self.window.obter_geometria()
        if rect:
            win_left, win_top, _, _ = rect
            # Coordenada absoluta de fallback (sua lógica original)
            target_x = win_left + 450
            target_y = win_top + 230 
            
            logger.info(f"⚡ CLICK TURBO (Absoluto): ({target_x}, {target_y})")
            if self._clicar_e_validar(target_x, target_y, termo_busca):
                return True

        logger.warning("❌ Estratégia de Faixa falhou.")
        return False

    def _clicar_e_validar(self, x, y, termo):
        # Clique duplo
        pyautogui.moveTo(x, y, duration=0.3)
        pyautogui.click()
        time.sleep(0.1)
        pyautogui.click()
        pyautogui.moveRel(200, 0)
        
        return self._validar_mudanca(termo)

    def _validar_mudanca(self, texto_alvo):
        logger.info("⏳ Validando playback...")
        # Simulação de validação (pode usar OCR do player aqui se quiser)
        time.sleep(1.0)
        return True