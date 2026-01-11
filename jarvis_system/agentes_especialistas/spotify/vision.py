import os
import easyocr
import pyautogui
import numpy as np
import cv2  # OpenCV para tratamento de imagem
from thefuzz import fuzz # Lógica difusa para textos aproximados

class VisionSystem:
    def __init__(self):
        self.reader = None
        # Caminho absoluto da imagem do botão
        self.img_play_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../img/play_spotify.png"))

    def carregar_ocr(self):
        """Carrega o modelo na memória (Singleton pattern)"""
        if not self.reader:
            print("👁️ [Visão] Inicializando Motor OCR e Carregando Modelos...")
            # gpu=True acelera MUITO se tiver NVIDIA. Se não, use False.
            self.reader = easyocr.Reader(['pt', 'en'], gpu=False, verbose=False)

    def _processar_imagem(self, imagem_np):
        """
        TRATAMENTO DE IMAGEM (A Mágica):
        Converte para escala de cinza, aumenta contraste e binariza.
        Isso faz o texto 'brilhar' para o OCR ler melhor em fundo escuro.
        """
        # 1. Escala de Cinza
        gray = cv2.cvtColor(imagem_np, cv2.COLOR_RGB2GRAY)
        
        # 2. Upscaling (Aumentar a imagem ajuda a ler textos pequenos)
        scale_percent = 150 # Aumenta em 50%
        width = int(gray.shape[1] * scale_percent / 100)
        height = int(gray.shape[0] * scale_percent / 100)
        dim = (width, height)
        resized = cv2.resize(gray, dim, interpolation=cv2.INTER_LINEAR)

        # 3. Binarização (Preto e Branco puro) - Threshold Adaptativo
        # Ótimo para lidar com o fundo degradê do Spotify
        binary = cv2.adaptiveThreshold(
            resized, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        return binary, scale_percent

    def ler_tela(self, region=None):
        """
        Lê o texto da tela.
        Args:
            region: Tupla (left, top, width, height). Se None, lê a tela toda.
        """
        self.carregar_ocr()
        
        # 1. Tira o print (Screenshot)
        if region:
            screenshot = pyautogui.screenshot(region=region)
        else:
            screenshot = pyautogui.screenshot()
            
        imagem_np = np.array(screenshot)

        # 2. Aplica o tratamento de imagem (OpenCV)
        imagem_processada, scale_factor = self._processar_imagem(imagem_np)

        # 3. OCR na imagem tratada
        # detail=1 retorna as coordenadas (bounding box)
        resultados_raw = self.reader.readtext(imagem_processada, detail=1)

        # 4. Ajusta as coordenadas de volta ao tamanho original (Desfaz o Upscale)
        resultados_ajustados = []
        fator = 100 / scale_factor

        for (bbox, texto, conf) in resultados_raw:
            # Ignora leituras com confiança muito baixa (< 30%)
            if conf < 0.3: continue
            
            # Recalcula as coordenadas da caixa
            (tl, tr, br, bl) = bbox
            tl = [int(tl[0] * fator), int(tl[1] * fator)]
            tr = [int(tr[0] * fator), int(tr[1] * fator)]
            br = [int(br[0] * fator), int(br[1] * fator)]
            bl = [int(bl[0] * fator), int(bl[1] * fator)]
            
            # Se usou region, precisa somar o offset X e Y da região
            offset_x, offset_y = (region[0], region[1]) if region else (0, 0)
            
            # Formata a nova bounding box ajustada
            new_bbox = ([tl[0]+offset_x, tl[1]+offset_y], 
                        [tr[0]+offset_x, tr[1]+offset_y], 
                        [br[0]+offset_x, br[1]+offset_y], 
                        [bl[0]+offset_x, bl[1]+offset_y])
            
            resultados_ajustados.append((new_bbox, texto, conf))

        return resultados_ajustados

    def encontrar_texto_fuzzy(self, texto_alvo, region=None, min_score=80):
        """
        Busca inteligente: Encontra texto mesmo com erros de digitação.
        Retorna: (Centro_X, Centro_Y) ou None
        """
        leituras = self.ler_tela(region)
        texto_alvo = texto_alvo.lower()
        
        melhor_candidato = None
        maior_score = 0

        for (bbox, texto_lido, conf) in leituras:
            texto_lido_lower = texto_lido.lower()
            
            # 1. Verifica similaridade parcial (Ex: "Linkin" dentro de "Linkin Park")
            score_parcial = fuzz.partial_ratio(texto_alvo, texto_lido_lower)
            
            # 2. Verifica similaridade total (Ex: "Play" vs "P1ay")
            score_ratio = fuzz.ratio(texto_alvo, texto_lido_lower)
            
            score_final = max(score_parcial, score_ratio)

            if score_final > maior_score and score_final >= min_score:
                maior_score = score_final
                melhor_candidato = bbox

        if melhor_candidato:
            print(f"👁️ [Visão] Texto encontrado (Score: {maior_score}%): '{texto_alvo}'")
            (tl, tr, br, bl) = melhor_candidato
            center_x = int((tl[0] + br[0]) / 2)
            center_y = int((tl[1] + br[1]) / 2)
            return (center_x, center_y)
        
        return None

    def procurar_botao_play(self, region=None):
        if os.path.exists(self.img_play_path):
            try:
                # Procura apenas na região especificada (mais rápido)
                return pyautogui.locateOnScreen(
                    self.img_play_path, 
                    confidence=0.8, 
                    grayscale=False, 
                    region=region
                )
            except: pass
        return None