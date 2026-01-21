import logging
import pyautogui
import time
from difflib import SequenceMatcher

# Tenta importar memória espacial para cache de coordenadas
try:
    from jarvis_system.cortex_motor.camera.spatial_memory import spatial_mem
except ImportError:
    spatial_mem = None

logger = logging.getLogger("STRATEGY_PLAYLIST")

class PlaylistStrategy:
    """
    Estratégia para tocar Playlists.
    Lógica similar à de Artistas (Entrar no perfil -> Clicar Play),
    mas forçando o filtro de Playlists e usando caches separados.
    """

    def __init__(self, vision, window, filter_manager):
        self.vision = vision
        self.window = window
        self.filter_manager = filter_manager

    def executar(self, termo_busca, anchor_point=None):
        logger.info(f"📂 [Estratégia] Abrindo playlist: '{termo_busca}'")
        
        # Preparação das chaves de cache e normalização
        termo_limpo = termo_busca.lower().strip()
        slug = termo_limpo.replace(' ', '_')
        
        # CHAVES DIFERENTES DO ARTISTA (Evita colisão de memória)
        self.cache_key_list = f"playlist_pos_{slug}"
        self.cache_key_play = f"play_btn_pos_playlist_{slug}"

        # 1. Garante que estamos na aba Playlists (Fallback de segurança)
        if not anchor_point:
            anchor_point = self.filter_manager.selecionar(["playlist", "playlists"])
        
        start_x, start_y = anchor_point if anchor_point else (400, 280)

        # Atualiza geometria
        rect = self.window.obter_geometria()
        self.win_left, self.win_top, self.win_right, self.win_bottom = rect if rect else (0, 0, 1920, 1080)
        self.width = self.win_right - self.win_left
        self.height = self.win_bottom - self.win_top

        # =========================================================
        # PASSO 1: ENCONTRAR E CLICAR NA PLAYLIST
        # =========================================================
        encontrou_item = False
        
        # 1.1 Sniper (Memória)
        if spatial_mem:
            coords = spatial_mem.buscar_coordenada(self.width, self.height, self.cache_key_list)
            if coords:
                abs_x = self.win_left + coords[0]
                abs_y = self.win_top + coords[1]
                
                logger.info(f"⚡ [Sniper Playlist] Lembrança para '{termo_busca}' em ({abs_x}, {abs_y}). Validando...")
                
                if self._validar_posicao_item(abs_x, abs_y, termo_busca):
                    logger.info(f"✅ [Sniper] Validação OK. Entrando.")
                    self._clique_simples(abs_x, abs_y)
                    encontrou_item = True
                else:
                    logger.warning(f"⚠️ [Sniper] Validação falhou. Iniciando varredura...")

        # 1.2 Canhão (Busca Visual)
        if not encontrou_item:
            base_x = self.win_left + 80 if rect else max(0, start_x - 450)
            region_results = (int(base_x), int(start_y + 60), 1000, 600)

            logger.info(f"👁️ Lendo lista de playlists para encontrar: '{termo_busca}'...")
            elementos = self.vision.ler_tela(region=region_results)
            
            candidato_x, candidato_y = None, None
            melhor_score = 0.0
            nome_encontrado = ""

            for bbox, texto_lido, conf in elementos:
                txt_norm = texto_lido.lower().strip()
                score = SequenceMatcher(None, txt_norm, termo_limpo).ratio()
                if termo_limpo in txt_norm: score = max(score, 0.95)

                if score > 0.75 and score > melhor_score:
                    melhor_score = score
                    nome_encontrado = texto_lido
                    (tl, tr, br, bl) = bbox
                    candidato_x = int((tl[0] + br[0]) / 2)
                    candidato_y = int((tl[1] + br[1]) / 2)

            if candidato_x and candidato_y:
                logger.info(f"🎯 ALVO CONFIRMADO: '{nome_encontrado}' ({int(melhor_score*100)}%). Entrando...")
                self._clique_simples(candidato_x, candidato_y)
                
                if spatial_mem:
                    rel_x = candidato_x - self.win_left
                    rel_y = candidato_y - self.win_top
                    logger.info(f"💾 [Memória] Aprendi onde fica a Playlist '{termo_busca}': ({rel_x}, {rel_y})")
                    spatial_mem.memorizar_coordenada(self.width, self.height, self.cache_key_list, rel_x, rel_y)
            else:
                logger.warning(f"⚠️ Nome '{termo_busca}' não lido. Usando clique cego fallback.")
                self._clique_simples(base_x + 100, start_y + 100)

        # =========================================================
        # PASSO 2: CLICAR NO PLAY
        # =========================================================
        return self._executar_play_sequence_com_memoria()

    def _executar_play_sequence_com_memoria(self):
        logger.info("⏳ Carregando playlist...")
        time.sleep(2.0) 
        
        # 2.1 Sniper Play (Memória)
        if spatial_mem:
            coords = spatial_mem.buscar_coordenada(self.width, self.height, self.cache_key_play)
            if coords:
                abs_x = self.win_left + coords[0]
                abs_y = self.win_top + coords[1]
                
                logger.info(f"⚡ [Sniper Play] Buscando botão verde em ({abs_x}, {abs_y})...")
                
                if self._validar_botao_play_na_posicao(abs_x, abs_y):
                    logger.info("✅ [Sniper Play] Botão confirmado! Clicando.")
                    self._clique_simples(abs_x, abs_y)
                    return True
                else:
                    logger.warning("⚠️ [Sniper Play] Botão não encontrado. Buscando visualmente...")

        # 2.2 Canhão Play (Busca Visual)
        logger.info("🟢 Procurando botão Play visualmente...")
        pos_encontrada = self._buscar_botao_verde_visualmente()
        
        if pos_encontrada:
            x, y = pos_encontrada
            logger.info(f"🎯 Botão Play encontrado. Coordenadas: ({x}, {y})")
            self._clique_simples(x, y)
            
            if spatial_mem:
                rel_x = x - self.win_left
                rel_y = y - self.win_top
                logger.info(f"💾 [Memória] Aprendi onde fica o Play desta Playlist: ({rel_x}, {rel_y})")
                spatial_mem.memorizar_coordenada(self.width, self.height, self.cache_key_play, rel_x, rel_y)
            return True
            
        logger.warning("⚠️ Play visual não achado. Tentando 'Enter' cego...")
        pyautogui.press('enter')
        return True

    def _validar_posicao_item(self, x, y, termo_alvo):
        w, h = 200, 60
        region = (max(0, int(x - w//2)), max(0, int(y - h//2)), int(w), int(h))
        try:
            resultado = self.vision.ler_tela(region=region)
            alvo_norm = termo_alvo.lower().strip()
            for _, texto, _ in resultado:
                txt_norm = texto.lower().strip()
                if alvo_norm in txt_norm or SequenceMatcher(None, txt_norm, alvo_norm).ratio() > 0.8:
                    return True
            return False
        except: return False

    def _validar_botao_play_na_posicao(self, x, y):
        w, h = 100, 100 
        region = (max(0, int(x - w//2)), max(0, int(y - h//2)), int(w), int(h))
        pos = self.vision.procurar_botao_play(region=region)
        return pos is not None

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
        if len(pos) == 4:
            return (pos[0] + pos[2] // 2, pos[1] + pos[3] // 2)
        return pos

    def _clique_simples(self, x, y):
        if x is None or y is None: return
        x, y = int(x), int(y)
        logger.info(f"🖱️ Clicando em ({x}, {y})...")
        pyautogui.moveTo(x, y, duration=0.6)
        pyautogui.click()
        time.sleep(0.5)
        pyautogui.moveRel(200, 0)