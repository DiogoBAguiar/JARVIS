import logging
import pyautogui
import time
import os
from difflib import SequenceMatcher

logger = logging.getLogger("SPOTIFY_FILTER")

class FilterManager:
    """
    Gerencia a barra de filtros do Spotify (Tudo, Músicas, Artistas, Podcasts, etc.).
    Centraliza a lógica de OCR e Geometria da barra superior.
    """

    def __init__(self, vision, window):
        self.vision = vision
        self.window = window

    def selecionar(self, nomes_alvo: list) -> tuple:
        """
        Busca um botão na barra de filtros que corresponda a um dos nomes na lista.
        Ex: nomes_alvo = ["música", "musica", "songs"]
        
        Retorna: (x, y) do clique ou None se falhar.
        """
        target_str = "/".join(nomes_alvo)
        logger.info(f"🧹 Buscando filtro: '{target_str}'...")

        # 1. Define a região da barra de filtros
        rect = self.window.obter_geometria()
        if not rect:
            logger.error("❌ Não foi possível obter geometria da janela.")
            return None

        win_left, win_top, win_right, _ = rect
        width = win_right - win_left
        
        # --- AJUSTE DE GEOMETRIA (CRÍTICO) ---
        # Margem Esquerda: 120px (pula ícones laterais, mas pega 'Tudo' e 'Artistas')
        # Antes era 300px, o que cortava os botões.
        sidebar_margin = 120
        
        # Offset Superior: 70px (pula barra de título e busca)
        # Foca exatamente na linha dos chips de filtro.
        top_offset = 70
        
        # Altura da Busca: 150px (suficiente para pegar a linha de botões)
        search_height = 150
        
        # Largura da Busca: 80% da tela restante (evita ler perfil/amigos na direita)
        search_width = int((width - sidebar_margin) * 0.8)
        
        region_top = (
            win_left + sidebar_margin, 
            win_top + top_offset, 
            search_width, 
            search_height
        )

        # --- DEBUG VISUAL ---
        # Salva o que o robô está vendo para diagnóstico
        try:
            debug_file = "debug_visao_filtro.png"
            # O pyautogui pode falhar em alguns ambientes headless, por isso o try/except
            pyautogui.screenshot(region=region_top).save(debug_file)
            logger.debug(f"📸 Debug visual salvo em: {debug_file}")
        except Exception as e:
            logger.warning(f"Falha ao salvar debug visual: {e}")

        # 2. Leitura OCR
        # O vision.ler_tela deve retornar as coordenadas.
        # Nota: Se o seu OCR retornar coordenadas relativas à imagem cortada, 
        # teremos que somar (win_left + sidebar_margin, win_top + top_offset) no final.
        # Assumindo aqui que ele retorna coordenadas de tela ou que lida com o offset internamente.
        elementos = self.vision.ler_tela(region=region_top)
        
        melhor_candidato = None
        melhor_score = 0.0
        texto_encontrado = ""

        # 3. Fuzzy Matching para encontrar o botão
        for bbox, texto, conf in elementos:
            txt_lower = texto.lower().strip()
            
            for alvo in nomes_alvo:
                # Compara similaridade (ajuda com erros de OCR como 'MUsicas')
                score = SequenceMatcher(None, txt_lower, alvo.lower()).ratio()
                
                # Se for match exato ou substring forte
                if alvo.lower() == txt_lower: score = 1.0
                elif alvo.lower() in txt_lower and len(txt_lower) < len(alvo) + 5: score = 0.95

                if score > 0.75 and score > melhor_score:
                    melhor_score = score
                    melhor_candidato = bbox
                    texto_encontrado = texto
                    logger.debug(f"   Candidato: '{texto}' ({score:.2f})")

        # 4. Clicar
        if melhor_candidato:
            (tl, tr, br, bl) = melhor_candidato
            cx = int((tl[0] + br[0]) / 2)
            cy = int((tl[1] + br[1]) / 2)
            
            logger.info(f"🔘 Filtro '{texto_encontrado}' encontrado ({int(melhor_score*100)}%): Clicando em ({cx}, {cy})")
            
            pyautogui.moveTo(cx, cy, duration=0.4)
            pyautogui.click()
            time.sleep(1.5) # Tempo para a lista carregar e animar
            return (cx, cy)

        logger.warning(f"❌ Filtro '{target_str}' não encontrado visualmente na região analisada.")
        return None