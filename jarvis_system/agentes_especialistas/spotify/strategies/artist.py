import logging
import pyautogui
import time

logger = logging.getLogger("STRATEGY_ARTIST")

class ArtistStrategy:
    """
    Estratégia Artista.
    Foca em clicar no card de perfil e buscar o botão Play verde.
    """

    def __init__(self, vision, window, filter_manager):
        self.vision = vision
        self.window = window
        self.filter_manager = filter_manager

    def executar(self, termo_busca, anchor_point=None):
        logger.info(f"🎨 [Estratégia] Entrando no perfil: '{termo_busca}'")
        
        perfil_entrado = False
        
        # 1. Clicar no Perfil (Card do Artista)
        if anchor_point:
            btn_x, btn_y = anchor_point
            
            # O card do artista fica um pouco abaixo dos filtros (~140px)
            target_y = btn_y + 140 
            
            rect = self.window.obter_geometria()
            target_x = btn_x
            if rect: target_x = rect[0] + 550 # Centralizado na área principal
            
            logger.info(f"⚡ CLICK TURBO (Relativo): ({target_x}, {target_y})")
            self._clique_simples(target_x, target_y)
            perfil_entrado = True
        else:
            # Fallback (Clique cego)
            rect = self.window.obter_geometria()
            if rect:
                wl, wt, _, _ = rect
                target_x = wl + 450
                target_y = wt + 250
                logger.info(f"📍 Clique cego perfil: ({target_x}, {target_y})")
                self._clique_simples(target_x, target_y)
                perfil_entrado = True

        if not perfil_entrado: return False

        # 2. Tocar (Botão Verde)
        logger.info("⏳ Aguardando perfil carregar...")
        time.sleep(3.5) # Tempo essencial para o botão verde aparecer
        
        logger.info("🟢 Procurando botão Play...")
        if self._clicar_botao_verde():
            return True
            
        # 3. Fallback final (Enter)
        logger.warning("⚠️ Play visual não achado. Tentando 'Enter' cego...")
        pyautogui.press('enter')
        time.sleep(0.5)
        return True

    def _clique_simples(self, x, y):
        pyautogui.moveTo(x, y, duration=0.4)
        pyautogui.click()
        pyautogui.moveRel(200, 0) # Tira mouse da frente

    def _clicar_botao_verde(self):
        """
        Tenta encontrar o botão Play verde usando a busca Multi-Escala.
        """
        # Tentativa 1: Busca Focada (Header do Artista)
        try:
            rect = self.window.obter_geometria()
            if rect:
                wl, wt, wr, wb = rect
                # Região generosa para garantir que a imagem caiba
                width = max(wr - wl - 300, 200) 
                region = (wl + 300, wt, width, 600)
                
                # O finder agora retorna (x, y) do centro, não um bbox
                pos = self.vision.procurar_botao_play(region=region)
                if pos:
                    self._click_point(pos)
                    return True
        except Exception as e:
            logger.warning(f"⚠️ Erro na busca focada: {e}")

        # Tentativa 2: Busca Global (Tela Toda)
        logger.info("🔍 Tentando busca global pelo botão Play...")
        try:
            pos = self.vision.procurar_botao_play()
            if pos:
                self._click_point(pos)
                return True
        except Exception as e:
            logger.error(f"❌ Erro na busca global: {e}")
            
        return False

    def _click_point(self, pos):
        """Clica em uma coordenada (x, y) direta."""
        x, y = pos # Desempacota a tupla diretamente (CORREÇÃO AQUI)
        
        logger.info(f"✅ Botão Play encontrado em ({x}, {y}). Clicando!")
        pyautogui.moveTo(x, y, duration=0.5) # Movimento um pouco mais lento para ser visível
        pyautogui.click()