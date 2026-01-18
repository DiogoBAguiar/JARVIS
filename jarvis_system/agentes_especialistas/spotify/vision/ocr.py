import logging
import pyautogui
import gc
from .dependencies import cv2, easyocr, np, DEPENDENCIES_OK

logger = logging.getLogger("VISION_OCR")

class OCRProcessor:
    """
    Responsável pelo processamento de imagem e extração de texto.
    Versão V4 (Speed-Focused): Otimizada para leitura rápida de UI.
    """
    
    _shared_reader = None

    def __init__(self):
        pass

    def carregar_modelo(self):
        if not DEPENDENCIES_OK: return False
        
        if OCRProcessor._shared_reader is None:
            logger.info("👁️ [OCR] Carregando modelo EasyOCR na memória...")
            try:
                # Se tiver GPU NVIDIA, mude gpu=False para True
                OCRProcessor._shared_reader = easyocr.Reader(['pt', 'en'], gpu=False, verbose=False)
                logger.info("✅ Motor OCR pronto.")
            except Exception as e:
                logger.error(f"❌ Falha ao carregar EasyOCR: {e}")
                return False
        return True

    def liberar_memoria(self):
        if OCRProcessor._shared_reader:
            logger.info("🧹 Liberando memória do OCR...")
            del OCRProcessor._shared_reader
            OCRProcessor._shared_reader = None
            gc.collect()

    def _processar_imagem(self, imagem_np, fast_mode=False):
        """
        Tratamento de imagem focado em performance.
        """
        if not DEPENDENCIES_OK or cv2 is None: return None, 100

        try:
            # 1. Conversão para Grayscale (Obrigatório)
            gray = cv2.cvtColor(imagem_np, cv2.COLOR_RGB2GRAY)
            
            # Se for modo rápido (ex: ler menus simples), retorna raw
            if fast_mode:
                return gray, 100

            # 2. Pipeline de Precisão (Apenas para Artistas/Capas difíceis)
            # Upscale Linear 1.5x é o sweet spot entre velocidade e leitura
            scale_percent = 150
            width = int(gray.shape[1] * scale_percent / 100)
            height = int(gray.shape[0] * scale_percent / 100)
            dim = (width, height)
            
            # INTER_LINEAR é muito mais rápido que CUBIC e suficiente para 90% dos casos
            processed = cv2.resize(gray, dim, interpolation=cv2.INTER_LINEAR)

            # 3. CLAHE (Vital para texto branco em fundo claro/colorido)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(processed)

            return enhanced, scale_percent

        except Exception as e:
            logger.error(f"Erro processando imagem: {e}")
            return None, 100

    def ler_tela(self, region=None, fast_mode=False):
        """
        Tira print e retorna lista de (bbox, texto, confiança).
        """
        if not self.carregar_modelo(): return []

        try:
            # Validação da região
            if region and any(x < 0 for x in region): region = None

            # 1. Captura (Gargalo de I/O)
            screenshot = pyautogui.screenshot(region=region)
            imagem_np = np.array(screenshot)

            # 2. Tratamento (Gargalo de CPU)
            imagem_proc, scale = self._processar_imagem(imagem_np, fast_mode=fast_mode)
            if imagem_proc is None: return []

            # 3. Leitura (Gargalo de IA)
            # paragraph=False é mais rápido para listas
            resultados_raw = OCRProcessor._shared_reader.readtext(
                imagem_proc, 
                detail=1,
                paragraph=False 
            )

            # 4. Normalização
            resultados_ajustados = []
            fator = 100 / scale
            ox, oy = (region[0], region[1]) if region else (0, 0)

            for (bbox, texto, conf) in resultados_raw:
                if conf < 0.35: continue 

                (tl, tr, br, bl) = bbox
                
                def adj(p): return [int(p[0] * fator) + ox, int(p[1] * fator) + oy]
                
                new_bbox = (adj(tl), adj(tr), adj(br), adj(bl))
                resultados_ajustados.append((new_bbox, texto, conf))

            return resultados_ajustados

        except Exception as e:
            logger.error(f"Erro no OCR: {e}")
            return []