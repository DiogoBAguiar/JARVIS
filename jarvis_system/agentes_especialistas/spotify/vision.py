import os
import logging
import numpy as np
import pyautogui

# Configuração de Logs
logger = logging.getLogger("SPOTIFY_VISION")

# Importações de Visão Computacional (Pesadas e Opcionais)
# O sistema não deve travar no boot se faltar uma lib de OCR
try:
    import cv2
    import easyocr
    from thefuzz import fuzz
    DEPENDENCIES_OK = True
except ImportError as e:
    logger.warning(f"⚠️ Módulo de visão degradado. Faltando dependências: {e}")
    DEPENDENCIES_OK = False
    cv2 = None
    easyocr = None
    fuzz = None

class VisionSystem:
    """
    Subsistema de Visão Computacional.
    Responsável por 'ver' a tela, processar imagens e ler textos (OCR).
    """
    def __init__(self):
        self.reader = None
        # Caminho relativo ajustado para dentro do módulo do agente
        # Agora busca em: jarvis_system/agentes_especialistas/spotify/img/play_spotify.png
        self.img_play_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "img", "play_spotify.png")
        )

    def _check_dependencies(self) -> bool:
        """Verifica se as dependências de visão estão instaladas."""
        if not DEPENDENCIES_OK:
            logger.error("Tentativa de usar visão computacional sem dependências (opencv/easyocr).")
            return False
        return True

    def carregar_ocr(self):
        """Carrega o modelo EasyOCR na memória (Lazy Loading)."""
        if not self._check_dependencies(): return

        if not self.reader:
            logger.info("👁️ [Visão] Carregando modelos de OCR (Isso pode levar alguns segundos)...")
            try:
                # gpu=True acelera muito, mas pode falhar se não houver CUDA configurado.
                # Mantemos False por estabilidade, ou tente True com fallback.
                self.reader = easyocr.Reader(['pt', 'en'], gpu=False, verbose=False)
                logger.info("✅ Motor OCR carregado.")
            except Exception as e:
                logger.error(f"❌ Falha crítica ao carregar EasyOCR: {e}")
                self.reader = None

    def _processar_imagem(self, imagem_np):
        """
        Pipeline de pré-processamento de imagem para melhorar o OCR.
        Aumenta contraste, remove ruído e binariza.
        """
        if not self._check_dependencies(): return None, 100

        try:
            # 1. Escala de Cinza
            gray = cv2.cvtColor(imagem_np, cv2.COLOR_RGB2GRAY)
            
            # 2. Upscaling (Aumentar a imagem ajuda a ler fontes pequenas da UI)
            scale_percent = 150 # 150% do tamanho original
            width = int(gray.shape[1] * scale_percent / 100)
            height = int(gray.shape[0] * scale_percent / 100)
            dim = (width, height)
            
            # Interpolação Linear é rápida e boa o suficiente
            resized = cv2.resize(gray, dim, interpolation=cv2.INTER_LINEAR)

            # 3. Binarização Adaptativa (Preto e Branco Inteligente)
            # Lida bem com fundos degradê ou não uniformes do Spotify
            binary = cv2.adaptiveThreshold(
                resized, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            return binary, scale_percent
        except Exception as e:
            logger.error(f"Erro no processamento de imagem: {e}")
            return None, 100

    def ler_tela(self, region=None):
        """
        Captura a tela e extrai textos com suas coordenadas.
        
        Args:
            region: Tupla (left, top, width, height) para capturar apenas um pedaço.
        
        Returns:
            List[Tuple]: Lista de (bbox, text, conf)
        """
        if not self._check_dependencies(): return []
        
        # Garante que o OCR está pronto
        self.carregar_ocr()
        if not self.reader: return []

        try:
            # 1. Screenshot
            if region:
                # Validação básica de região para evitar erro do pyautogui
                if any(x < 0 for x in region): region = None
                
            screenshot = pyautogui.screenshot(region=region)
            imagem_np = np.array(screenshot)

            # 2. Tratamento
            imagem_processada, scale_percent = self._processar_imagem(imagem_np)
            if imagem_processada is None: return []

            # 3. Inferência OCR
            # detail=1 retorna as bounding boxes
            resultados_raw = self.reader.readtext(imagem_processada, detail=1)

            # 4. Normalização de Coordenadas
            resultados_ajustados = []
            fator_escala = 100 / scale_percent # Inverso do upscale

            offset_x, offset_y = (region[0], region[1]) if region else (0, 0)

            for (bbox, texto, conf) in resultados_raw:
                # Filtro de confiança (Ignora lixo)
                if conf < 0.4: continue # Subi um pouco a régua para 40%
                
                # Desfaz o upscale nas coordenadas
                (tl, tr, br, bl) = bbox
                
                # Função auxiliar para ajustar ponto
                def adj(point):
                    return [int(point[0] * fator_escala) + offset_x, 
                            int(point[1] * fator_escala) + offset_y]

                new_bbox = (adj(tl), adj(tr), adj(br), adj(bl))
                
                resultados_ajustados.append((new_bbox, texto, conf))

            return resultados_ajustados

        except Exception as e:
            logger.error(f"Erro durante leitura de tela (OCR): {e}")
            return []

    def encontrar_texto_fuzzy(self, texto_alvo: str, region=None, min_score=80):
        """
        Localiza coordenadas de um texto na tela usando correspondência aproximada.
        Útil para quando o OCR erra uma letra ou outra (ex: 'Spotfy' vs 'Spotify').
        """
        if not self._check_dependencies(): return None

        leituras = self.ler_tela(region)
        if not leituras: return None

        texto_alvo = texto_alvo.lower()
        melhor_bbox = None
        maior_score = 0

        for (bbox, texto_lido, conf) in leituras:
            texto_lido_lower = texto_lido.lower()
            
            # Similaridade parcial ("Rock" in "Classic Rock")
            score_parcial = fuzz.partial_ratio(texto_alvo, texto_lido_lower)
            # Similaridade total ("Mettalica" vs "Metallica")
            score_ratio = fuzz.ratio(texto_alvo, texto_lido_lower)
            
            score_final = max(score_parcial, score_ratio)

            if score_final > maior_score and score_final >= min_score:
                maior_score = score_final
                melhor_bbox = bbox

        if melhor_bbox:
            logger.info(f"👁️ Texto encontrado: '{texto_alvo}' (Confiança Fuzzy: {maior_score}%)")
            # Calcula o centro da bounding box
            (tl, tr, br, bl) = melhor_bbox
            center_x = int((tl[0] + br[0]) / 2)
            center_y = int((tl[1] + br[1]) / 2)
            return (center_x, center_y)
        
        return None

    def procurar_botao_play(self, region=None):
        """
        Busca visual pura por template matching (imagem do botão).
        Mais rápido que OCR, mas menos flexível.
        """
        if not os.path.exists(self.img_play_path):
            logger.warning(f"Imagem de referência não encontrada: {self.img_play_path}")
            return None

        try:
            # PyAutoGUI usa OpenCV por baixo dos panos para confidence
            return pyautogui.locateOnScreen(
                self.img_play_path, 
                confidence=0.8, 
                grayscale=False, 
                region=region
            )
        except pyautogui.ImageNotFoundException:
            # Erro comum, não precisa logar como erro
            return None
        except Exception as e:
            logger.error(f"Erro na busca visual de botão: {e}")
            return None