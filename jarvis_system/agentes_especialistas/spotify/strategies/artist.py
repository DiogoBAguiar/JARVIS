import logging
import pyautogui
import time
from difflib import SequenceMatcher

logger = logging.getLogger("STRATEGY_ARTIST")

class ArtistStrategy:
    """
    Estratégia Artista: Busca visualmente o nome do artista na lista de resultados
    antes de clicar, evitando cliques errados em sugestões do Spotify.
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
        
        # Define ponto de partida base (se o filtro falhou, chuta o meio)
        start_x, start_y = anchor_point if anchor_point else (300, 250)

        # 2. DEFINIÇÃO DA REGIÃO DE BUSCA (OCR)
        # Olhamos para a área abaixo dos filtros onde os cards aparecem
        region_results = (
            max(0, start_x - 100),  # X: Um pouco à esquerda do filtro
            start_y + 60,           # Y: Logo abaixo dos filtros
            600,                    # Largura: Suficiente para o nome do artista
            500                     # Altura: Vê os primeiros 3-4 resultados
        )

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
            
            # Bonificação se o nome exato estiver contido (ex: "Coldplay" em "This Is Coldplay")
            if alvo_limpo in texto_limpo: 
                score = max(score, 0.95)

            # Debug para ajuste fino
            if score > 0.6:
                logger.debug(f"   Analisando: '{texto_lido}' (Score: {score:.2f})")

            if score > 0.75 and score > melhor_score:
                melhor_score = score
                nome_encontrado = texto_lido
                
                # Calcula o centro do clique baseado na caixa de texto encontrada
                (tl, tr, br, bl) = bbox
                # Assumindo que OCR retorna coordenadas absolutas (padrão EasyOCR/Vision Wrapper)
                # Se for relativo, somar region_results[0] e [1]
                candidato_x = int((tl[0] + br[0]) / 2)
                candidato_y = int((tl[1] + br[1]) / 2)

        # 4. AÇÃO DE CLIQUE (INTELIGENTE OU FALLBACK)
        if candidato_x and candidato_y:
            logger.info(f"🎯 ALVO CONFIRMADO: '{nome_encontrado}' ({int(melhor_score*100)}%). Clicando...")
            self._clique_simples(candidato_x, candidato_y)
        else:
            # Fallback: Se o OCR não ler nada (ex: imagem do artista sem texto), usa o clique cego
            logger.warning(f"⚠️ Nome '{termo_busca}' não lido. Usando clique cego no 1º resultado.")
            # Ajuste de coordenadas cegas (mais seguro)
            blind_x = start_x
            blind_y = start_y + 150 
            self._clique_simples(blind_x, blind_y)

        # 5. Tocar (Botão Verde)
        logger.info("⏳ Carregando perfil...")
        time.sleep(3.0) # Espera a animação de transição de página
        
        logger.info("🟢 Procurando botão Play...")
        if self._clicar_botao_verde():
            return True
            
        # Fallback final (Enter)
        logger.warning("⚠️ Play visual não achado. Tentando 'Enter' cego...")
        pyautogui.press('enter')
        return True

    def _clique_simples(self, x, y):
        """Movimento humanoide para clicar"""
        pyautogui.moveTo(x, y, duration=0.6) # Movimento mais suave
        pyautogui.click()
        time.sleep(0.5)
        pyautogui.moveRel(200, 0) # Tira o mouse de cima para não atrapalhar leitura futura

    def _clicar_botao_verde(self):
        """Busca o botão verde de play em toda a tela ou região focada"""
        # Tenta buscar na área comum de cabeçalho primeiro
        try:
            rect = self.window.obter_geometria()
            if rect:
                wl, wt, wr, wb = rect
                # Foca na metade esquerda superior, onde o botão play costuma ficar
                region_play = (wl, wt + 100, int((wr-wl)*0.8), 500)
                pos = self.vision.procurar_botao_play(region=region_play)
                if pos:
                    self._click_point(pos)
                    return True
        except: pass

        # Busca Global se a focada falhar
        pos = self.vision.procurar_botao_play()
        if pos:
            self._click_point(pos)
            return True
        return False

    def _click_point(self, pos):
        x, y = pos
        logger.info(f"✅ Botão Play encontrado em ({x}, {y}). Clicando!")
        pyautogui.moveTo(x, y, duration=0.5)
        pyautogui.click()