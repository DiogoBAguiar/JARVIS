import logging
import pyautogui
import gc # Garbage Collector para limpeza de RAM
from .dependencies import cv2, easyocr, np, DEPENDENCIES_OK

logger = logging.getLogger("VISION_OCR")

class OCRProcessor:
    """
    Responsável pelo processamento de imagem e extração de texto.
    Versão Otimizada: Suporta 'Fast Mode' e Descarregamento de Memória.
    """

    def __init__(self):
        self.reader = None

    def carregar_modelo(self):
        """Lazy loading do modelo EasyOCR (pesado)."""
        if not DEPENDENCIES_OK: return False
        
        if not self.reader:
            logger.info("👁️ [OCR] Carregando modelo EasyOCR na memória (Isso gasta RAM)...")
            try:
                # gpu=False garante compatibilidade, mude para True se tiver CUDA configurado
                self.reader = easyocr.Reader(['pt', 'en'], gpu=False, verbose=False)
                logger.info("✅ Motor OCR pronto.")
            except Exception as e:
                logger.error(f"❌ Falha ao carregar EasyOCR: {e}")
                self.reader = None
                return False
        return True

    def liberar_memoria(self):
        """
        NOVO: Descarrega o modelo para liberar ~500MB de RAM quando ocioso.
        """
        if self.reader:
            logger.info("🧹 Liberando memória do OCR (Garbage Collection)...")
            del self.reader
            self.reader = None
            gc.collect() # Força limpeza imediata do Python

    def _processar_imagem(self, imagem_np, fast_mode=False):
        """
        Pipeline: Grayscale -> (Opcional) Upscale -> Binarização Adaptativa.
        
        Args:
            fast_mode (bool): Se True, pula o upscale. Mais rápido, mas menos preciso para fontes miúdas.
        """
        if not DEPENDENCIES_OK or cv2 is None: return None, 100

        try:
            # 1. Escala de Cinza
            gray = cv2.cvtColor(imagem_np, cv2.COLOR_RGB2GRAY)
            
            scale_percent = 100 # Padrão (Sem zoom)

            # 2. Upscaling (Só faz se NÃO for modo rápido)
            # Otimização: Evita redimensionar se o texto já for grande ou performance for crítica
            if not fast_mode:
                scale_percent = 150
                width = int(gray.shape[1] * scale_percent / 100)
                height = int(gray.shape[0] * scale_percent / 100)
                dim = (width, height)
                
                processed = cv2.resize(gray, dim, interpolation=cv2.INTER_LINEAR)
            else:
                processed = gray

            # 3. Binarização (Preto e Branco Inteligente)
            binary = cv2.adaptiveThreshold(
                processed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            return binary, scale_percent
        except Exception as e:
            logger.error(f"Erro processando imagem: {e}")
            return None, 100

    def ler_tela(self, region=None, fast_mode=False):
        """
        Tira print e retorna lista de (bbox, texto, confiança).
        Agora suporta o parâmetro 'fast_mode' para leituras rápidas.
        """
        if not self.carregar_modelo(): return []

        try:
            # Validação da região
            if region and any(x < 0 for x in region): region = None

            # 1. Captura
            screenshot = pyautogui.screenshot(region=region)
            imagem_np = np.array(screenshot)

            # 2. Tratamento (Com ou sem upscale)
            imagem_proc, scale = self._processar_imagem(imagem_np, fast_mode=fast_mode)
            if imagem_proc is None: return []

            # 3. Leitura
            resultados_raw = self.reader.readtext(imagem_proc, detail=1)

            # 4. Normalização (Desfaz o zoom do processamento para retornar coords reais)
            resultados_ajustados = []
            fator = 100 / scale
            ox, oy = (region[0], region[1]) if region else (0, 0)

            for (bbox, texto, conf) in resultados_raw:
                if conf < 0.4: continue # Filtro de confiança

                (tl, tr, br, bl) = bbox
                
                # Ajusta coordenadas locais da imagem redimensionada para globais da tela
                def adj(p): return [int(p[0] * fator) + ox, int(p[1] * fator) + oy]
                
                new_bbox = (adj(tl), adj(tr), adj(br), adj(bl))
                resultados_ajustados.append((new_bbox, texto, conf))

            return resultados_ajustados

        except Exception as e:
            logger.error(f"Erro no OCR: {e}")
            return []