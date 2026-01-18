import time
import logging
from .ocr import OCRProcessor
from .finder import VisualFinder

logger = logging.getLogger("VISION_SYSTEM")

class VisionSystem:
    """
    Subsistema de Visão Computacional (Fachada).
    Orquestra OCR e Localização Visual com Polling Inteligente.
    """
    def __init__(self):
        # Composição: O sistema TEM um processador OCR e um Localizador
        self.ocr = OCRProcessor()
        self.finder = VisualFinder(self.ocr)

    # --- MÉTODOS IMEDIATOS (OLHADA RÁPIDA) ---

    def ler_tela(self, region=None, otimizar_velocidade=False):
        """
        Proxy para o processador de OCR.
        Args:
            otimizar_velocidade (bool): Se True, desativa o upscale (zoom) para ser mais rápido.
        """
        return self.ocr.ler_tela(region, fast_mode=otimizar_velocidade)

    def procurar_botao_play(self, region=None):
        """Proxy para busca de imagem."""
        return self.finder.procurar_botao_play(region)
    
    def encontrar_texto_fuzzy(self, texto_alvo, region=None, min_score=80):
        """Proxy para busca inteligente de texto."""
        return self.finder.encontrar_texto_fuzzy(texto_alvo, region, min_score)

    def carregar_ocr(self):
        """Força o carregamento dos modelos na memória."""
        self.ocr.carregar_modelo()

    # --- NOVOS MÉTODOS DE ESPERA (POLLING VISUAL) ---
    # Isso elimina a necessidade de time.sleep() fixos no controller

    def esperar_botao_play(self, timeout=5.0, region=None):
        """
        Bloqueia a execução até o botão play aparecer ou o tempo esgotar.
        Retorna: Coordenadas (x, y) ou None.
        """
        logger.info(f"👁️ Aguardando botão Play aparecer (Max {timeout}s)...")
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            pos = self.finder.procurar_botao_play(region)
            if pos:
                return pos
            time.sleep(0.2) # Breve pausa para não sobrecarregar a CPU
            
        logger.warning("timeout: Botão Play não apareceu.")
        return None

    def esperar_texto(self, texto, timeout=5.0, region=None):
        """
        Bloqueia a execução até um texto específico aparecer na tela.
        Retorna: Coordenadas (x, y) ou None.
        """
        logger.info(f"👁️ Aguardando texto '{texto}'... (Max {timeout}s)")
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            # Usa um score levemente mais permissivo (75) para detecção rápida
            res = self.finder.encontrar_texto_fuzzy(texto, region, min_score=75)
            if res:
                return res
            time.sleep(0.5)
            
        return None