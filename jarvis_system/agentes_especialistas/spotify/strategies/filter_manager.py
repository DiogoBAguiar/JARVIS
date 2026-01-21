import logging
import pyautogui
import time
import os
from difflib import SequenceMatcher

# Tenta importar memória espacial para cache de coordenadas
try:
    from jarvis_system.cortex_motor.camera.spatial_memory import spatial_mem
except ImportError:
    spatial_mem = None

logger = logging.getLogger("SPOTIFY_FILTER")

class FilterManager:
    """
    Gerencia a barra de filtros do Spotify (Tudo, Músicas, Artistas, Podcasts).
    
    VERSÃO 5.0 (Dual-Slot Memory):
    - Armazena até 2 posições conhecidas para cada filtro (Principal e Alternativa).
    - Se o layout muda (ex: sidebar abre/fecha), ele tenta a posição alternativa antes de escanear.
    - Implementa rotação de memória: Nova -> Principal, Antiga Principal -> Alternativa.
    """

    def __init__(self, vision, window):
        self.vision = vision
        self.window = window

    def selecionar(self, nomes_alvo: list) -> tuple:
        """
        Busca um botão na barra de filtros.
        Retorna: (x, y) do clique ou None.
        """
        target_str = "/".join(nomes_alvo)
        termo_principal = nomes_alvo[0] # Ex: "artista"
        
        # Chaves de Cache (Slots 1 e 2)
        key_primary = f"filter_btn_{termo_principal}"
        key_backup = f"filter_btn_{termo_principal}_alt"

        # 1. Define a geometria da janela
        rect = self.window.obter_geometria()
        if not rect:
            logger.error("❌ Não foi possível obter geometria da janela.")
            return None

        win_left, win_top, win_right, win_bottom = rect
        width = win_right - win_left
        height = win_bottom - win_top

        # =========================================================
        # FASE 1: SNIPER DUPLO (Verifica Principal, depois Backup)
        # =========================================================
        if spatial_mem:
            # 1.1 Tenta Slot Principal
            if self._tentar_sniper(width, height, win_left, win_top, key_primary, nomes_alvo, "Principal"):
                return self._recuperar_abs(width, height, win_left, win_top, key_primary)

            # 1.2 Tenta Slot Backup (Se o layout mudou para um estado anterior)
            if self._tentar_sniper(width, height, win_left, win_top, key_backup, nomes_alvo, "Backup"):
                # Se o backup funcionou, o ideal seria promover ele, mas mantemos simples por enquanto
                return self._recuperar_abs(width, height, win_left, win_top, key_backup)

        # =========================================================
        # FASE 2: CANHÃO (Busca Visual Completa + Rotação de Memória)
        # =========================================================
        logger.info(f"🧹 [Canhão] Nenhuma memória válida. Iniciando varredura visual para: '{target_str}'...")
        
        # Configuração da Região de Busca
        sidebar_margin = 120
        top_offset = 70
        search_height = 150
        search_width = int((width - sidebar_margin) * 0.9) # Aumentei um pouco a largura
        
        region_top = (
            win_left + sidebar_margin, 
            win_top + top_offset, 
            search_width, 
            search_height
        )

        elementos = self.vision.ler_tela(region=region_top)
        
        melhor_candidato = None
        melhor_score = 0.0
        texto_encontrado = ""

        # Fuzzy Matching
        for bbox, texto, conf in elementos:
            txt_lower = texto.lower().strip()
            for alvo in nomes_alvo:
                score = SequenceMatcher(None, txt_lower, alvo.lower()).ratio()
                if alvo.lower() == txt_lower: score = 1.0
                elif alvo.lower() in txt_lower and len(txt_lower) < len(alvo) + 5: score = 0.95

                if score > 0.75 and score > melhor_score:
                    melhor_score = score
                    melhor_candidato = bbox
                    texto_encontrado = texto

        # Se encontrou: Clica e Atualiza Memória (Rotação)
        if melhor_candidato:
            (tl, tr, br, bl) = melhor_candidato
            cx_box = int((tl[0] + br[0]) / 2)
            cy_box = int((tl[1] + br[1]) / 2)
            
            # Ajuste de coordenadas (OCR relativo ao crop)
            final_x = cx_box
            final_y = cy_box
            if cx_box < region_top[0]:
                final_x += region_top[0]
                final_y += region_top[1]
            
            logger.info(f"🔘 Filtro '{texto_encontrado}' encontrado ({int(melhor_score*100)}%): Clicando em ({final_x}, {final_y})")
            self._clicar(final_x, final_y)
            
            # --- ROTAÇÃO DE MEMÓRIA ---
            if spatial_mem:
                rel_x = final_x - win_left
                rel_y = final_y - win_top
                
                # 1. Recupera o que estava no slot Principal antigo
                coords_old_primary = spatial_mem.buscar_coordenada(width, height, key_primary)
                
                # 2. Se existia algo antes, move para o Backup (preserva a história)
                if coords_old_primary:
                    # Só move se for diferente da nova posição (evita duplicar)
                    if abs(coords_old_primary[0] - rel_x) > 20 or abs(coords_old_primary[1] - rel_y) > 20:
                        logger.info(f"💾 [Memória] Movendo coordenada antiga para Backup (Slot 2).")
                        spatial_mem.memorizar_coordenada(width, height, key_backup, coords_old_primary[0], coords_old_primary[1])

                # 3. Salva a nova posição como Principal
                logger.info(f"💾 [Memória] Salvando nova posição Principal (Slot 1): ({rel_x}, {rel_y})")
                spatial_mem.memorizar_coordenada(width, height, key_primary, rel_x, rel_y)

            return (final_x, final_y)

        logger.warning(f"❌ Filtro '{target_str}' não encontrado visualmente.")
        return None

    def _tentar_sniper(self, w, h, wl, wt, key, keywords, slot_name):
        """Helper para validar uma coordenada da memória."""
        coords = spatial_mem.buscar_coordenada(w, h, key)
        if coords:
            abs_x = wl + coords[0]
            abs_y = wt + coords[1]
            
            logger.info(f"⚡ [Sniper {slot_name}] Verificando ({abs_x}, {abs_y})...")
            
            if self._validar_posicao(abs_x, abs_y, keywords):
                logger.info(f"✅ [Sniper {slot_name}] Validação OK! Clicando.")
                self._clicar(abs_x, abs_y)
                return True
            else:
                logger.warning(f"⚠️ [Sniper {slot_name}] Falhou. O botão não está aqui.")
        return False

    def _recuperar_abs(self, w, h, wl, wt, key):
        coords = spatial_mem.buscar_coordenada(w, h, key)
        if coords: return (wl + coords[0], wt + coords[1])
        return None

    def _validar_posicao(self, x, y, keywords):
        """Validação Visual Rápida (Recorte pequeno)"""
        w, h = 140, 60 
        left = max(0, x - w//2)
        top = max(0, y - h//2)
        region = (left, top, w, h)
        
        try:
            resultado = self.vision.ler_tela(region=region)
            for _, texto, _ in resultado:
                if any(k.lower() in texto.lower() for k in keywords):
                    return True
                if any(SequenceMatcher(None, texto.lower(), k.lower()).ratio() > 0.8 for k in keywords):
                    return True
            return False
        except: return False

    def _clicar(self, x, y):
        x, y = int(x), int(y)
        pyautogui.moveTo(x, y, duration=0.4)
        pyautogui.click()
        time.sleep(2.5) # Tempo para transição de UI