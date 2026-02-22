import time
import logging
import os
import glob
import pyautogui

from .ocr import OCRProcessor
from .finder import VisualFinder

logger = logging.getLogger("VISION_SYSTEM")

class VisionSystem:
    """
    Subsistema de Visão Computacional (Fachada).
    Orquestra OCR e Localização Visual com Polling Inteligente.
    """
    def __init__(self, debug_mode=True):
        self.ocr = OCRProcessor()
        self.finder = VisualFinder(self.ocr)
        self.debug_mode = debug_mode
        self.debug_dir = "debug_vision"
        
        if self.debug_mode:
            os.makedirs(self.debug_dir, exist_ok=True)
            self._limpar_pasta_debug()
            logger.info(f"📸 Modo de Debug Visual Ativado. Imagens serão substituídas em './{self.debug_dir}/'")

    def _limpar_pasta_debug(self):
        """Limpa as imagens da execução anterior na inicialização para não acumular lixo."""
        try:
            arquivos = glob.glob(os.path.join(self.debug_dir, "*.png"))
            for arquivo in arquivos:
                os.remove(arquivo)
        except Exception as e:
            logger.warning(f"Não foi possível limpar a pasta de debug: {e}")

    def _salvar_debug(self, region, prefix="visao"):
        """Salva a imagem exata do que o robô está a ver, sobrescrevendo a anterior."""
        if not self.debug_mode: return
        try:
            # Substituímos o timestamp (que criava milhares de ficheiros) por um sufixo fixo "_latest"
            filename = os.path.join(self.debug_dir, f"{prefix}_latest.png")
            
            if region:
                r = (int(region[0]), int(region[1]), int(region[2]), int(region[3]))
                if r[2] > 0 and r[3] > 0:
                    img = pyautogui.screenshot(region=r)
                    img.save(filename)
                    # Comentado para não poluir o terminal, já que sabemos que funciona
                    # logger.info(f"📸 Debug salvo: {filename} | {r}") 
                else:
                    logger.warning(f"⚠️ Impossível salvar debug, região com altura/largura <= 0: {r}")
            else:
                img = pyautogui.screenshot()
                img.save(filename)
        except Exception as e:
            logger.error(f"Erro ao salvar print de debug: {e}")

    # --- MÉTODOS IMEDIATOS (OLHADA RÁPIDA) ---

    def ler_tela(self, region=None, otimizar_velocidade=False):
        self._salvar_debug(region, prefix="ocr_canhao")
        return self.ocr.ler_tela(region, fast_mode=otimizar_velocidade)

    def procurar_botao_play(self, region=None):
        self._salvar_debug(region, prefix="finder_play")
        return self.finder.procurar_botao_play(region)
    
    def encontrar_texto_fuzzy(self, texto_alvo, region=None, min_score=80):
        self._salvar_debug(region, prefix="finder_texto")
        return self.finder.encontrar_texto_fuzzy(texto_alvo, region, min_score)

    def carregar_ocr(self):
        self.ocr.carregar_modelo()

    # --- MÉTODOS DE ESPERA (POLLING VISUAL) ---

    def esperar_botao_play(self, timeout=5.0, region=None):
        logger.info(f"👁️ Aguardando botão Play aparecer (Max {timeout}s)...")
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            pos = self.finder.procurar_botao_play(region)
            if pos: return pos
            time.sleep(0.2)
        logger.warning("timeout: Botão Play não apareceu.")
        return None

    def esperar_texto(self, texto, timeout=5.0, region=None):
        logger.info(f"👁️ Aguardando texto '{texto}'... (Max {timeout}s)")
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            res = self.finder.encontrar_texto_fuzzy(texto, region, min_score=75)
            if res: return res
            time.sleep(0.5)
        return None