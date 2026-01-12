import logging
import pyautogui
import time
import re

logger = logging.getLogger("STRATEGY_ARTIST")

class ArtistStrategy:
    """
    Estratégia Artista v6 (Map-Based Anchoring).
    Usa qualquer botão visível (Tudo, Músicas, etc.) para triangular a posição de 'Artistas'.
    """

    def __init__(self, vision, window):
        self.vision = vision
        self.window = window

    def executar(self, termo_busca):
        logger.info(f"🎨 [Estratégia] Iniciando modo Artista para: '{termo_busca}'")
        
        # 1. Tenta ativar o filtro 'Artistas' usando Mapeamento
        coords_filtro = self._ativar_filtro_artistas_mapeado()
        
        pyautogui.moveRel(0, 200) 
        
        perfil_entrado = False
        
        if coords_filtro:
            # Lógica Relativa
            btn_x, btn_y = coords_filtro
            target_x = btn_x 
            target_y = btn_y + 130 
            
            # Centraliza X na janela
            rect = self.window.obter_geometria()
            if rect: target_x = rect[0] + 550 
            
            logger.info(f"⚡ CLICK TURBO (Relativo): ({target_x}, {target_y})")
            self._clique_simples(target_x, target_y)
            perfil_entrado = True
            
        else:
            # Fallback Geométrico Total (Último recurso se nenhum texto for lido)
            logger.warning("⚠️ Nenhum texto lido na barra. Usando Coordenada Fixa.")
            rect = self.window.obter_geometria()
            if rect:
                wl, wt, _, _ = rect
                # Posição fixa estimada do botão 'Artistas' na janela padrão
                # Sidebar (300) + Margem (160) = 460
                filter_x = wl + 460
                filter_y = wt + 140 # Altura aproximada da barra de filtros
                
                logger.info(f"📍 Tentando clique cego no filtro Artistas: ({filter_x}, {filter_y})")
                self._clique_simples(filter_x, filter_y)
                time.sleep(2.0)
                
                # Agora tenta clicar no perfil
                target_x = wl + 400
                target_y = wt + 220
                self._clique_simples(target_x, target_y)
                perfil_entrado = True
            else:
                return False

        if not perfil_entrado: return False

        # --- ETAPA 2: TOCAR ---
        logger.info("⏳ Aguardando perfil...")
        time.sleep(3.5)
        
        logger.info("🟢 Procurando botão Play...")
        if self._clicar_botao_verde():
            return True
            
        logger.warning("⚠️ Play visual não achado. Tentando 'Enter' cego...")
        pyautogui.press('enter')
        time.sleep(1.0)
        
        pyautogui.press('tab')
        time.sleep(0.1)
        pyautogui.press('enter')
        
        return True

    def _ativar_filtro_artistas_mapeado(self):
        logger.info("🧹 Mapeando barra de filtros...")
        
        rect = self.window.obter_geometria()
        if not rect: return None
        win_left, win_top, win_right, _ = rect
        width = win_right - win_left
        
        # Ignora sidebar (300px)
        sidebar_margin = 300
        search_width = width - sidebar_margin
        region_top = (win_left + sidebar_margin, win_top, search_width, 300)

        elementos = self.vision.ler_tela(region=region_top)
        
        # MAPA DE DISTÂNCIAS (Offsets em X até o botão 'Artistas')
        # Se achar a chave, soma o valor ao X encontrado.
        mapa_offsets = {
            'artista': 0, 'artistas': 0, 'artist': 0, 'artists': 0, # O próprio
            'música': 90, 'musica': 90, 'músicas': 90, 'songs': 90, # Vizinho esquerdo
            'tudo': 160, 'all': 160 # Primeiro item
        }

        # 1. Procura o MELHOR candidato (Prioriza 'Artistas', depois 'Músicas', depois 'Tudo')
        melhor_candidato = None
        menor_prioridade = 999 
        
        # Define prioridades (0=Melhor, 2=Pior)
        prioridades = {'artista': 0, 'música': 1, 'tudo': 2} 

        for bbox, texto, _ in elementos:
            txt = texto.lower()
            
            # Verifica se o texto contém alguma chave do mapa
            for chave, offset in mapa_offsets.items():
                if chave in txt:
                    # Define a prioridade baseada na raiz da palavra
                    prio = 2
                    if 'artist' in chave: prio = 0
                    elif 'music' in chave or 'músic' in chave: prio = 1
                    
                    if prio < menor_prioridade:
                        melhor_candidato = (bbox, offset, chave)
                        menor_prioridade = prio
        
        # 2. Executa a ação baseada no melhor candidato encontrado
        if melhor_candidato:
            bbox, offset_x, chave_encontrada = melhor_candidato
            (tl, tr, br, bl) = bbox
            cx = int((tl[0] + br[0]) / 2)
            cy = int((tl[1] + br[1]) / 2)
            
            alvo_x = cx + offset_x
            
            if offset_x == 0:
                logger.info(f"✅ Filtro EXATO encontrado: '{chave_encontrada}'.")
            else:
                logger.info(f"⚓ Âncora '{chave_encontrada}' encontrada. Triangulando Artistas (+{offset_x}px).")
            
            self._clicar_filtro(alvo_x, cy)
            return (alvo_x, cy)

        logger.warning("⚠️ Nenhum ponto de referência encontrado na barra.")
        return None

    def _clicar_filtro(self, x, y):
        pyautogui.moveTo(x, y, duration=0.4)
        pyautogui.click()
        time.sleep(2.0) 

    def _clicar_botao_verde(self):
        try:
            rect = self.window.obter_geometria()
            if rect:
                wl, wt, wr, wb = rect
                region = (wl + 300, wt, wr - wl - 300, int((wb-wt)/1.5))
                pos = self.vision.procurar_botao_play(region=region)
            else:
                pos = self.vision.procurar_botao_play()
                
            if pos:
                x, y = pyautogui.center(pos)
                pyautogui.moveTo(x, y, duration=0.3)
                pyautogui.click()
                return True
        except: pass
        return False

    def _clique_simples(self, x, y):
        pyautogui.moveTo(x, y, duration=0.4)
        time.sleep(0.1)
        pyautogui.click()
        pyautogui.moveRel(200, 0)