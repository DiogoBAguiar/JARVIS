import time
import logging
import subprocess
import pyautogui

# Importação condicional para evitar quebra em ambientes não-Windows (CI/CD ou Linux)
try:
    import win32gui
except ImportError:
    win32gui = None

# Dependências Internas (Ajuste de imports relativos devido à nova pasta)
# Agora estamos dentro de spotify/controller/, então subimos um nível a mais (..)
from ..window import WindowManager
from ..input import InputManager
from ..vision import VisionSystem

# Configuração de Logs
logger = logging.getLogger("SPOTIFY_CONTROLLER")

class SpotifyController:
    """
    Controlador Híbrido: Combina automação de API/Processo com Inteligência Visual.
    Usa VisionSystem para 'ver' o botão de play e OCR para ler faixas.
    """
    
    def __init__(self):
        self.window = WindowManager()
        self.input = InputManager()
        self.vision = VisionSystem()

    def launch_app(self, timeout: int = 15) -> bool:
        """
        Inicia o Spotify e garante que a janela está focada e pronta.
        
        Args:
            timeout (int): Tempo limite para desistir da inicialização.
        """
        logger.info("🚀 [Controller] Inicializando Spotify...")
        
        try:
            # Protocolo 'spotify:' é mais robusto que caminhos de arquivo absolutos
            subprocess.run("start spotify:", shell=True)
            
            # Polling Ativo: Espera inteligente pela janela
            start_time = time.time()
            while time.time() - start_time < timeout:
                hwnd = self.window.obter_hwnd()
                if hwnd:
                    logger.info("✅ Janela detectada. Focando...")
                    # Pequeno delay para renderização da UI (evita clicar no nada)
                    time.sleep(1.5) 
                    if self._preparar_janela():
                        return True
                time.sleep(1)
            
            logger.error(f"❌ Timeout ({timeout}s) aguardando janela do Spotify.")
            return False

        except Exception as e:
            logger.error(f"❌ Falha crítica ao lançar app: {e}")
            return False

    def _preparar_janela(self):
        """Garante foco na janela e retorna o handle (HWND)."""
        hwnd = self.window.obter_hwnd()
        if hwnd:
            try:
                self.window.focar(hwnd)
                return hwnd
            except Exception as e:
                logger.warning(f"⚠️ Erro ao focar janela: {e}")
        return None

    def _obter_regiao_janela(self, hwnd):
        """
        Calcula geometria da janela para otimizar o OCR.
        Ler apenas a região da janela aumenta a performance em 10x vs Tela Cheia.
        """
        if not hwnd or not win32gui: return None
        try:
            rect = win32gui.GetWindowRect(hwnd) # (left, top, right, bottom)
            w = rect[2] - rect[0]
            h = rect[3] - rect[1]
            return (rect[0], rect[1], w, h)
        except Exception as e:
            logger.error(f"Erro ao calcular região da janela: {e}")
            return None

    def _obter_regiao_player(self, hwnd):
        """
        Calcula a região do 'Now Playing' (canto inferior esquerdo).
        Estratégia: Pegar os últimos 15% da altura e os primeiros 30% da largura.
        """
        regiao_total = self._obter_regiao_janela(hwnd)
        if not regiao_total: return None
        
        x, y, w, h = regiao_total
        
        # Geometria empírica do Spotify Desktop
        player_h = int(h * 0.15) # Barra inferior
        player_w = int(w * 0.30) # Área do texto da música
        
        player_x = x
        player_y = y + h - player_h
        
        return (player_x, player_y, player_w, player_h)

    def ler_musica_atual(self):
        """
        Usa OCR para ler o que está tocando agora.
        Retorna: dict {'titulo': str, 'artista': str} ou None
        """
        hwnd = self._preparar_janela()
        if not hwnd: return None
        
        regiao_player = self._obter_regiao_player(hwnd)
        if not regiao_player: return None
        
        logger.info("👀 Lendo região do Player...")
        # Usa o VisionSystem para ler apenas aquele pedacinho da tela
        leituras = self.vision.ler_tela(region=regiao_player)
        
        if not leituras: return None
        
        # Heurística simples: O maior texto costuma ser o título, o menor o artista
        # Ou simplesmente concatena tudo o que achou
        textos = [t[1] for t in leituras if len(t[1]) > 2] # Filtra ruído curto
        
        if not textos: return None
        
        # Assume formato: Título em cima, Artista embaixo
        info = {
            "titulo": textos[0],
            "artista": textos[1] if len(textos) > 1 else "Desconhecido",
            "raw": " - ".join(textos)
        }
        logger.info(f"🎵 Música Identificada: {info['raw']}")
        return info

    def buscar_e_clicar(self, texto_alvo: str, tentar_rolagem: bool = True) -> bool:
        """
        Busca visual avançada usando Fuzzy Logic no OCR.
        """
        hwnd = self._preparar_janela()
        if not hwnd: return False
        
        # Otimização: Restringe visão à janela do app
        regiao = self._obter_regiao_janela(hwnd)
        
        logger.info(f"🕵️ [Controller] Buscando visualmente: '{texto_alvo}'")
        max_tentativas = 3 if tentar_rolagem else 1

        for tentativa in range(max_tentativas):
            try:
                # Busca Fuzzy (Aceita erros como 'Metallca' em vez de 'Metallica')
                coords_tela = self.vision.encontrar_texto_fuzzy(texto_alvo, region=regiao)
                
                if coords_tela:
                    cx, cy = coords_tela
                    
                    # Converte coordenadas Globais (Tela) -> Locais (Janela) para clique seguro
                    if win32gui:
                        pl = win32gui.ScreenToClient(hwnd, (int(cx), int(cy)))
                        self.input.clique_fantasma_com_enter(hwnd, pl[0], pl[1])
                    else:
                        # Fallback simples se win32gui falhar
                        pyautogui.click(cx, cy)
                        pyautogui.press('enter')
                        
                    logger.info(f"🎯 Alvo encontrado e clicado na tentativa {tentativa + 1}.")
                    return True
                
                if tentar_rolagem and tentativa < max_tentativas - 1:
                    logger.debug("📉 Rolando tela para buscar mais resultados...")
                    self.input.rolar_tela("down", 1)
                    time.sleep(0.5) # Estabiliza UI pós-scroll
                    # Atualiza região pois janela pode ter movido (raro, mas defensivo)
                    regiao = self._obter_regiao_janela(hwnd)
            
            except Exception as e:
                logger.error(f"Erro durante busca visual: {e}")
                break # Aborta loop em erro crítico

        return False

    def play_search(self, query: str):
        """
        Fluxo principal de execução: Busca -> Identifica -> Toca.
        """
        if not self.launch_app():
            return "Falha ao iniciar aplicação."

        hwnd = self._preparar_janela()
        
        try:
            # 1. Input de Busca
            self.input.digitar_atalho_busca(query)
            logger.info("⏳ Aguardando renderização dos resultados...")
            time.sleep(2.5) # Crítico: Spotify demora a carregar busca via rede

            regiao = self._obter_regiao_janela(hwnd)

            # 2. Visão Computacional: Botão Verde (Prioridade Alta)
            botao = self.vision.procurar_botao_play(region=regiao)
            
            if botao:
                logger.info("🟢 Botão 'Play' verde identificado.")
                centro = pyautogui.center(botao)
                if win32gui:
                    pl = win32gui.ScreenToClient(hwnd, (centro.x, centro.y))
                    self.input.clique_fantasma_com_enter(hwnd, pl[0], pl[1])
                else:
                    pyautogui.click(centro)
                return "Tocando via reconhecimento visual."

            # 3. OCR Fuzzy: Texto da Música (Prioridade Média)
            logger.warning("⚠️ Botão Play não encontrado. Tentando OCR no texto...")
            if self.buscar_e_clicar(query, tentar_rolagem=False):
                return "Tocando via leitura de texto."

            # 4. Fallback Cego (Teclado)
            logger.warning("⌨️ Falha visual total. Acionando modo cego (Tab+Enter).")
            pyautogui.press('tab')
            time.sleep(0.1)
            pyautogui.press('enter')
            return "Tocando via atalhos de teclado (fallback)."

        except Exception as e:
            logger.error(f"Erro no fluxo de reprodução: {e}")
            return f"Erro: {str(e)}"

    # --- Proxy Methods (Interface Simplificada) ---
    def resume(self): self.input.midia("play_pause")
    def pause(self): self.input.midia("play_pause")
    def next_track(self): self.input.midia("next")
    def previous_track(self): self.input.midia("prev")
    def scroll(self, direction): self.input.rolar_tela(direction)
    def curtir_musica(self): self.input.midia("like") # Adicionado para suportar o fluxo de "Gostei"