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
    Gerencia a barra de filtros do Spotify (Tudo, Músicas, Artistas, Podcasts, etc.).
    
    LÓGICA HÍBRIDA (Sniper & Canhão):
    1. Tenta usar coordenada salva (Sniper).
    2. Se a validação visual da coordenada falhar (ou não existir), faz varredura completa (Canhão).
    3. Se encontrar na varredura, ATUALIZA a memória para corrigir o erro futuro.
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
        cache_key = f"filter_btn_{termo_principal}"

        # 1. Define a geometria da janela
        rect = self.window.obter_geometria()
        if not rect:
            logger.error("❌ Não foi possível obter geometria da janela.")
            return None

        win_left, win_top, win_right, win_bottom = rect
        width = win_right - win_left
        height = win_bottom - win_top

        # =========================================================
        # FASE 1: SNIPER (Tenta Cache + Validação Visual Rápida)
        # =========================================================
        if spatial_mem:
            coords = spatial_mem.buscar_coordenada(width, height, cache_key)
            if coords:
                abs_x = win_left + coords[0]
                abs_y = win_top + coords[1]
                
                logger.info(f"⚡ [Sniper] Cache existe para '{termo_principal}'. Validando posição ({abs_x}, {abs_y})...")
                
                # Valida visualmente apenas aquele pedacinho (Debug Específico)
                if self._validar_posicao(abs_x, abs_y, nomes_alvo, termo_principal):
                    logger.info(f"✅ [Sniper] Validação visual OK. Clicando.")
                    self._clicar(abs_x, abs_y)
                    return (abs_x, abs_y)
                else:
                    logger.warning(f"⚠️ [Sniper] Validação falhou (Botão moveu ou layout mudou). Iniciando correção...")
                    # Se falhou, não retorna! Deixa cair para a FASE 2 para corrigir.

        # =========================================================
        # FASE 2: CANHÃO (Busca Visual Completa + Correção de Cache)
        # =========================================================
        logger.info(f"🧹 [Canhão] Iniciando varredura visual para: '{target_str}'...")
        
        # --- Configuração da Região de Busca ---
        sidebar_margin = 120
        top_offset = 70
        search_height = 150
        search_width = int((width - sidebar_margin) * 0.8)
        
        region_top = (
            win_left + sidebar_margin, 
            win_top + top_offset, 
            search_width, 
            search_height
        )

        # Leitura OCR da região
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

        # Se encontrou na varredura -> Clica e CORRIGE O CACHE
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
            
            # --- APRENDIZADO / CORREÇÃO ---
            if spatial_mem:
                rel_x = final_x - win_left
                rel_y = final_y - win_top
                logger.info(f"💾 [Correção] Atualizando Memória Espacial: '{cache_key}' -> ({rel_x}, {rel_y})")
                spatial_mem.memorizar_coordenada(width, height, cache_key, rel_x, rel_y)

            return (final_x, final_y)

        logger.warning(f"❌ Filtro '{target_str}' não encontrado visualmente na região analisada.")
        return None

    def _validar_posicao(self, x, y, keywords, nome_debug):
        """
        Validação 'Sniper': Tira print minúsculo da área prevista para confirmar texto.
        Isso evita cliques cegos em posições obsoletas.
        """
        w, h = 140, 60 # Janela pequena de validação (um pouco maior para margem de erro)
        left = max(0, x - w//2)
        top = max(0, y - h//2)
        region = (left, top, w, h)
        
        try:
            # DEBUG: Salva o que o sniper está vendo
            # nome_arquivo = f"debug_sniper_{nome_debug}.png"
            # pyautogui.screenshot(region=region).save(nome_arquivo)
            
            resultado = self.vision.ler_tela(region=region)
            
            for _, texto, _ in resultado:
                # Verifica palavras chave
                if any(k.lower() in texto.lower() for k in keywords):
                    return True
                # Match parcial forte
                if any(SequenceMatcher(None, texto.lower(), k.lower()).ratio() > 0.8 for k in keywords):
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Erro na validação visual (Sniper): {e}")
            return False

    def _clicar(self, x, y):
        pyautogui.moveTo(x, y, duration=0.4)
        pyautogui.click()
        # Tempo estendido para garantir a transição da UI (resolve erro Linkin Park)
        time.sleep(2.5)