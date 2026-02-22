import logging
import pyautogui
import time
from difflib import SequenceMatcher

try:
    from jarvis_system.cortex_motor.camera.spatial_memory import spatial_mem
except ImportError:
    spatial_mem = None

logger = logging.getLogger("STRATEGY_ARTIST")

class ArtistStrategy:
    """
    Estratégia Artista V7.2 (Consciência de Estado):
    - Entende quando a música já está a tocar (Pause detectado) e aborta o Enter cego.
    """

    def __init__(self, vision, window, filter_manager):
        self.vision = vision
        self.window = window
        self.filter_manager = filter_manager

    def executar(self, termo_busca, anchor_point=None):
        logger.info(f"🎨 [Estratégia] Entrando no perfil: '{termo_busca}'")
        
        time.sleep(2.0) 
        
        termo_limpo = termo_busca.lower().strip()
        slug = termo_limpo.replace(' ', '_')
        
        self.cache_key_artist = f"artist_pos_{slug}"
        self.cache_key_play = f"play_btn_pos_{slug}"

        if not anchor_point:
            anchor_point = self.filter_manager.selecionar(["artista", "artists", "artistas"])
        
        logger.info("⏳ Aguardando lista de artistas carregar na tela...")
        time.sleep(2.0)
        
        start_x, start_y = anchor_point if anchor_point else (400, 150)

        rect = self.window.obter_geometria()
        self.win_left, self.win_top, self.win_right, self.win_bottom = rect if rect else (0, 0, 1920, 1080)
        self.width = self.win_right - self.win_left
        self.height = self.win_bottom - self.win_top

        # =========================================================
        # PASSO 1: ENCONTRAR E CLICAR NO ARTISTA
        # =========================================================
        encontrou_artista = False
        
        if spatial_mem:
            coords = spatial_mem.buscar_coordenada(self.width, self.height, self.cache_key_artist)
            if coords:
                abs_x = self.win_left + coords[0]
                abs_y = self.win_top + coords[1]
                
                logger.info(f"⚡ [Sniper Artista] Lembrança em ({abs_x}, {abs_y}). Validando...")
                
                if self._validar_posicao_artista(abs_x, abs_y, termo_busca):
                    logger.info(f"✅ [Sniper] Validação OK. Entrando no perfil.")
                    self._clique_simples(abs_x, abs_y)
                    encontrou_artista = True
                else:
                    logger.warning(f"⚠️ [Sniper] Memória corrompida. Rejeitado!")
                    if hasattr(spatial_mem, 'esquecer_coordenada'):
                        spatial_mem.esquecer_coordenada(self.cache_key_artist)

        if not encontrou_artista:
            base_x = self.win_left + 50 if rect else max(0, start_x - 450)
            altura_visao = 300 
            region_results = (int(base_x), int(start_y + 50), 1000, altura_visao)

            logger.info(f"👁️ Lendo APENAS o topo da lista para: '{termo_busca}'...")
            elementos = self.vision.ler_tela(region=region_results)
            
            candidato_x, candidato_y = None, None
            melhor_score = 0.0
            nome_encontrado = ""

            for bbox, texto_lido, conf in elementos:
                txt_norm = texto_lido.lower().strip()
                score = SequenceMatcher(None, txt_norm, termo_limpo).ratio()
                
                if termo_limpo in txt_norm: 
                    score = max(score, 0.95)

                if score > 0.70 and score > melhor_score:
                    melhor_score = score
                    nome_encontrado = texto_lido
                    (tl, tr, br, bl) = bbox
                    candidato_x = int((tl[0] + br[0]) / 2)
                    candidato_y = int((tl[1] + br[1]) / 2)

            if candidato_x and candidato_y:
                logger.info(f"🎯 ALVO TOP RESULT CONFIRMADO: '{nome_encontrado}'. Entrando...")
                self._clique_simples(candidato_x, candidato_y)
                
                if spatial_mem:
                    rel_x = candidato_x - self.win_left
                    rel_y = candidato_y - self.win_top
                    spatial_mem.memorizar_coordenada(self.width, self.height, self.cache_key_artist, rel_x, rel_y)
            else:
                logger.warning(f"⚠️ Não consegui ler '{termo_busca}'. Tentando clique cego no 1º card...")
                self._clique_simples(start_x, start_y + 150)

        # =========================================================
        # PASSO 2: ENCONTRAR E CLICAR NO PLAY
        # =========================================================
        return self._executar_play_sequence_com_memoria()

    def _executar_play_sequence_com_memoria(self):
        logger.info("⏳ Carregando página do perfil do artista...")
        time.sleep(3.0) 
        
        if spatial_mem:
            coords = spatial_mem.buscar_coordenada(self.width, self.height, self.cache_key_play)
            if coords:
                abs_x = self.win_left + coords[0]
                abs_y = self.win_top + coords[1]
                
                logger.info(f"⚡ [Sniper Play] Buscando botão em ({abs_x}, {abs_y})...")
                
                pos_valida = self._validar_botao_play_na_posicao(abs_x, abs_y)
                
                if pos_valida == "ALREADY_PLAYING":
                    logger.info("✅ [Sniper Play] A música já está tocando (Botão Pause detectado). Missão cumprida!")
                    return True
                elif pos_valida is not None:
                    logger.info("✅ [Sniper Play] Botão confirmado visualmente! Clicando.")
                    self._clique_simples(abs_x, abs_y)
                    return True
                else:
                    logger.warning("⚠️ [Sniper Play] Botão mudou de sítio.")
                    if hasattr(spatial_mem, 'esquecer_coordenada'):
                        spatial_mem.esquecer_coordenada(self.cache_key_play)

        logger.info("🟢 Procurando botão Play visualmente...")
        pos_encontrada = self._buscar_botao_verde_visualmente()
        
        if pos_encontrada == "ALREADY_PLAYING":
            logger.info("🎯 A música já está tocando (Botão Pause detectado). Missão cumprida!")
            return True
        elif pos_encontrada:
            x, y = pos_encontrada
            logger.info(f"🎯 Botão Play encontrado. Clicando em ({x}, {y})")
            self._clique_simples(x, y)
            
            if spatial_mem:
                rel_x = x - self.win_left
                rel_y = y - self.win_top
                spatial_mem.memorizar_coordenada(self.width, self.height, self.cache_key_play, rel_x, rel_y)
            return True
            
        logger.warning("⚠️ Play visual não achado. Tentando 'Enter' cego...")
        pyautogui.press('enter')
        return True

    def _validar_posicao_artista(self, x, y, termo_alvo):
        w, h = 250, 80
        region = (max(0, int(x - w//2)), max(0, int(y - h//2)), int(w), int(h))
        try:
            resultado = self.vision.ler_tela(region=region)
            alvo_norm = termo_alvo.lower().strip()
            for _, texto, _ in resultado:
                txt_norm = texto.lower().strip()
                if ";" in txt_norm: continue
                if txt_norm == alvo_norm or SequenceMatcher(None, txt_norm, alvo_norm).ratio() > 0.85:
                    return True
            return False
        except: return False

    def _validar_botao_play_na_posicao(self, x, y):
        w, h = 100, 100 
        region = (max(0, int(x - w//2)), max(0, int(y - h//2)), int(w), int(h))
        # Agora retorna exatamente o que o finder.py responder
        return self.vision.procurar_botao_play(region=region)

    def _buscar_botao_verde_visualmente(self):
        try:
            region_play = (self.win_left, self.win_top + 150, int(self.width * 0.8), 500)
            pos = self.vision.procurar_botao_play(region=region_play)
            if pos: return self._centro(pos)
        except: pass
        pos = self.vision.procurar_botao_play()
        if pos: return self._centro(pos)
        return None

    def _centro(self, pos):
        # Repassa a string "ALREADY_PLAYING" sem tentar fazer matemática nela
        if isinstance(pos, str): return pos 
        if pos and len(pos) == 4:
            return (pos[0] + pos[2] // 2, pos[1] + pos[3] // 2)
        return pos

    def _clique_simples(self, x, y):
        if x is None or y is None: return
        x, y = int(x), int(y)
        logger.info(f"🖱️ Clicando em ({x}, {y})...")
        pyautogui.moveTo(x, y, duration=0.8)
        pyautogui.click()
        time.sleep(0.5)
        pyautogui.moveRel(200, 0)