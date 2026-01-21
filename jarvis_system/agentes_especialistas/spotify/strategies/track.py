import logging
import pyautogui
import time
from difflib import SequenceMatcher

# Tenta importar memória espacial
try:
    from jarvis_system.cortex_motor.camera.spatial_memory import spatial_mem
except ImportError:
    spatial_mem = None

logger = logging.getLogger("STRATEGY_TRACK")

class TrackStrategy:
    """
    Estratégia para tocar Músicas (Tracks) - V5.2 (Header Anchor).
    
    Lógica:
    1. Encontra a linha de cabeçalho (#, Título, Álbum, Relógio).
    2. Usa essa linha como âncora visual e de memória.
    3. Calcula o clique para a linha IMEDIATAMENTE ABAIXO (a primeira música).
    """

    def __init__(self, vision, window, filter_manager):
        self.vision = vision
        self.window = window
        self.filter_manager = filter_manager
        # Termos que identificam a linha de cabeçalho inconfundivelmente
        self.header_keywords = ["#", "título", "title", "álbum", "album", "duração"]

    def executar(self, termo_busca, anchor_point=None):
        logger.info(f"🎹 [Estratégia] Iniciando modo Faixa para: '{termo_busca}'")
        
        pyautogui.moveRel(0, 200) # Limpa visão
        
        rect = self.window.obter_geometria()
        if not rect: return False
        win_left, win_top, win_right, win_bottom = rect
        width = win_right - win_left
        height = win_bottom - win_top

        # Define X base (Centro da área de conteúdo)
        base_x = anchor_point[0] if anchor_point else (win_left + 450)
        
        # Chave de Memória para o CABEÇALHO (não para a música)
        cache_key_header = "ui_pos_track_list_header"
        
        header_y = None

        # =========================================================
        # FASE 1: SNIPER (Memória do Cabeçalho)
        # =========================================================
        if spatial_mem:
            coords = spatial_mem.buscar_coordenada(width, height, cache_key_header)
            if coords:
                abs_y = win_top + coords[1]
                logger.info(f"⚡ [Sniper Header] Verificando cabeçalho em Y={abs_y}...")
                
                # Valida se o cabeçalho ainda está lá
                if self._validar_eh_cabecalho(base_x, abs_y):
                    logger.info("✅ [Sniper] Cabeçalho confirmado visualmente.")
                    header_y = abs_y
                else:
                    logger.warning("⚠️ [Sniper] Cabeçalho não encontrado na memória. Recalculando...")

        # =========================================================
        # FASE 2: CANHÃO (Scanner de Cabeçalho)
        # =========================================================
        if not header_y:
            logger.info("🔭 Escaneando tela para encontrar a linha de cabeçalho (#, Título)...")
            
            # Área de busca: Abaixo do filtro até uns 300px para baixo
            start_scan_y = (anchor_point[1] + 20) if anchor_point else (win_top + 150)
            
            region_list = (
                int(base_x - 200),      # X: Largo o suficiente para pegar "Título" e "Álbum"
                int(start_scan_y),      # Y
                400,                    # W
                250                     # H
            )

            elementos = self.vision.ler_tela(region=region_list)
            
            for bbox, texto, conf in elementos:
                txt_lower = texto.lower().strip()
                
                # Se encontrar qualquer palavra chave de cabeçalho
                if any(k in txt_lower for k in self.header_keywords):
                    (tl, tr, br, bl) = bbox
                    found_y = int((tl[1] + br[1]) / 2)
                    
                    # Ajuste coordenadas relativas
                    if found_y < region_list[1]: found_y += region_list[1]
                    
                    logger.info(f"🎯 Cabeçalho detectado: '{texto}' em Y={found_y}")
                    header_y = found_y
                    
                    # Memoriza onde está o cabeçalho
                    if spatial_mem:
                        rel_y = header_y - win_top
                        spatial_mem.memorizar_coordenada(width, height, cache_key_header, 450, rel_y)
                    break

        # =========================================================
        # FASE 3: O CLIQUE (Cálculo do Offset)
        # =========================================================
        if header_y:
            # A mágica: Cabeçalho Y + 60px (altura segura da linha) = Primeira Música
            track_y = header_y + 60 
            logger.info(f"📐 Calculando alvo: Cabeçalho ({header_y}) + 60px -> Música ({track_y})")
            return self._clicar_duplo_cego(base_x, track_y, termo_busca)
        
        else:
            # Fallback total se não achar nem o cabeçalho
            logger.warning("⚠️ Cabeçalho não encontrado. Usando fallback geométrico cego.")
            fallback_y = (anchor_point[1] + 110) if anchor_point else (win_top + 230)
            return self._clicar_duplo_cego(base_x, fallback_y, termo_busca)

    def _validar_eh_cabecalho(self, x, y):
        """Lê a linha e retorna True APENAS se encontrar palavras de cabeçalho."""
        w, h = 300, 50
        region = (max(0, int(x - w//2)), max(0, int(y - 25)), int(w), int(h))
        try:
            res = self.vision.ler_tela(region=region)
            for _, texto, _ in res:
                if any(k in texto.lower() for k in self.header_keywords):
                    return True
            return False
        except:
            return False

    def _clicar_duplo_cego(self, x, y, termo):
        x, y = int(x), int(y)
        
        logger.info(f"⚡ CLICK DUPLO (Play) na Música em ({x}, {y})")
        pyautogui.moveTo(x, y, duration=0.3)
        pyautogui.click()
        time.sleep(0.05)
        pyautogui.click()
        
        pyautogui.moveRel(200, 0) # Tira o mouse
        
        logger.info("⏳ Validando playback...")
        time.sleep(1.0)
        return True