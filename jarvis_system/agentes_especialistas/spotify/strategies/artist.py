import logging
import pyautogui
import time
from difflib import SequenceMatcher

logger = logging.getLogger("STRATEGY_ARTIST")

class ArtistStrategy:
    """
    Estratégia Artista: Busca visualmente o nome do artista na lista de resultados
    antes de clicar, com suporte a debug visual e geometria ajustada à janela.
    
    VERSÃO ESTÁVEL (V4.0):
    - Removeu Cache Espacial (perigoso para elementos dinâmicos).
    - Usa Região de Interesse (ROI) para performance segura.
    """

    def __init__(self, vision, window, filter_manager):
        self.vision = vision
        self.window = window
        self.filter_manager = filter_manager

    def executar(self, termo_busca, anchor_point=None):
        logger.info(f"🎨 [Estratégia] Entrando no perfil: '{termo_busca}'")
        
        # 1. Garante que estamos na aba Artistas
        if not anchor_point:
            anchor_point = self.filter_manager.selecionar(["artista", "artists", "artistas"])
        
        # Define ponto de partida base (Y é o mais importante aqui)
        start_x, start_y = anchor_point if anchor_point else (400, 280)

        # 2. DEFINIÇÃO DA REGIÃO DE BUSCA (OCR)
        # Tenta pegar a geometria da janela para começar logo após a sidebar.
        
        base_x = 0 # Default (canto esquerdo da tela)
        rect = self.window.obter_geometria()
        if rect:
            wl, wt, wr, wb = rect
            base_x = wl + 80 # Pula a sidebar (ícones laterais)
        else:
            base_x = max(0, start_x - 450) # Fallback

        region_results = (
            int(base_x),                     # X: Começa na esquerda da área de conteúdo
            int(start_y + 60),               # Y: Logo abaixo dos filtros
            1000,                            # W: largo para pegar várias colunas
            600                              # H
        )

        # --- DEBUG VISUAL ---
        try:
            debug_file = "debug_visao_artista.png"
            # pyautogui.screenshot(region=region_results).save(debug_file)
            # logger.info(f"📸 Debug visual salvo em: {debug_file}")
        except Exception: pass

        # 3. ESCANEAMENTO VISUAL
        logger.info(f"👁️ Lendo resultados para encontrar: '{termo_busca}'...")
        elementos = self.vision.ler_tela(region=region_results)
        
        candidato_x, candidato_y = None, None
        melhor_score = 0.0
        nome_encontrado = ""

        for bbox, texto_lido, conf in elementos:
            # Normalização para comparação
            texto_limpo = texto_lido.lower().strip()
            alvo_limpo = termo_busca.lower().strip()

            # Lógica de Similaridade
            score = SequenceMatcher(None, texto_limpo, alvo_limpo).ratio()
            
            # Bonificação se o nome exato estiver contido
            if alvo_limpo in texto_limpo: 
                score = max(score, 0.95)

            if score > 0.75 and score > melhor_score:
                melhor_score = score
                nome_encontrado = texto_lido
                
                # Calcula o centro do clique baseado na caixa de texto encontrada
                (tl, tr, br, bl) = bbox
                
                # OCR geralmente retorna coords absolutas, mas se for relativo ajustamos:
                # Assumindo coords absolutas do EasyOCR
                candidato_x = int((tl[0] + br[0]) / 2)
                candidato_y = int((tl[1] + br[1]) / 2)

        # 4. AÇÃO DE CLIQUE
        if candidato_x and candidato_y:
            logger.info(f"🎯 ALVO CONFIRMADO: '{nome_encontrado}' ({int(melhor_score*100)}%). Clicando...")
            self._clique_simples(candidato_x, candidato_y)
        else:
            # Fallback Seguro
            logger.warning(f"⚠️ Nome '{termo_busca}' não lido. Usando clique cego no 1º resultado.")
            blind_x = base_x + 100 
            blind_y = start_y + 100 
            logger.info(f"📍 Tentando clique geométrico em ({blind_x}, {blind_y})")
            self._clique_simples(blind_x, blind_y)

        # 5. Tocar
        logger.info("⏳ Carregando perfil...")
        time.sleep(2.0)
        
        logger.info("🟢 Procurando botão Play...")
        if self._clicar_botao_verde():
            return True
            
        logger.warning("⚠️ Play visual não achado. Tentando 'Enter' cego...")
        pyautogui.press('enter')
        return True

    def _clique_simples(self, x, y):
        if x is None or y is None: return
        pyautogui.moveTo(x, y, duration=0.6)
        pyautogui.click()
        time.sleep(0.5)
        pyautogui.moveRel(200, 0) # Tira mouse de cima

    def _clicar_botao_verde(self):
        # Tenta com ROI otimizado (cabeçalho esquerdo)
        try:
            rect = self.window.obter_geometria()
            if rect:
                wl, wt, wr, wb = rect
                # Região provável do botão play: lado esquerdo, topo da janela
                region_play = (wl, wt + 150, int((wr-wl)*0.8), 500)
                pos = self.vision.procurar_botao_play(region=region_play)
                if pos:
                    self._click_point(pos)
                    return True
        except: pass

        # Fallback: Tela toda
        pos = self.vision.procurar_botao_play()
        if pos:
            self._click_point(pos)
            return True
        return False

    def _click_point(self, pos):
        # Lida com tupla (x, y) ou (x, y, w, h)
        if len(pos) == 4:
            x = pos[0] + pos[2] // 2
            y = pos[1] + pos[3] // 2
        else:
            x, y = pos
            
        logger.info(f"✅ Botão Play encontrado em ({x}, {y}). Clicando!")
        pyautogui.moveTo(x, y, duration=0.5)
        pyautogui.click()