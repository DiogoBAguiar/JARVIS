from .ocr import OCRProcessor
from .finder import VisualFinder

class VisionSystem:
    """
    Subsistema de Visão Computacional (Fachada).
    Orquestra OCR e Localização Visual.
    """
    def __init__(self):
        # Composição: O sistema TEM um processador OCR e um Localizador
        self.ocr = OCRProcessor()
        self.finder = VisualFinder(self.ocr)

    def ler_tela(self, region=None):
        """Proxy para o processador de OCR."""
        return self.ocr.ler_tela(region)

    def procurar_botao_play(self, region=None):
        """Proxy para busca de imagem."""
        return self.finder.procurar_botao_play(region)
    
    # --- CORREÇÃO AQUI: Adicionado min_score ---
    def encontrar_texto_fuzzy(self, texto_alvo, region=None, min_score=80):
        """Proxy para busca inteligente de texto."""
        # Repassa o min_score para o finder
        return self.finder.encontrar_texto_fuzzy(texto_alvo, region, min_score)

    def carregar_ocr(self):
        """Força o carregamento dos modelos na memória."""
        self.ocr.carregar_modelo()