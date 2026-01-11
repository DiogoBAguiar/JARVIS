import time
import logging
import pyautogui

# Importação condicional para evitar quebra em ambientes Linux/Mac
try:
    import win32gui
    import win32api
    import win32con
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False

# Configuração de Logs
logger = logging.getLogger("SPOTIFY_INPUT")

class InputManager:
    """
    Gerenciador de Entradas (Teclado/Mouse).
    Traduz intenções lógicas em eventos de hardware simulados.
    """

    @staticmethod
    def clique_fantasma_com_enter(hwnd, x_local, y_local):
        """
        Realiza um clique em segundo plano (PostMessage) seguido de Enter.
        Isso permite interagir com a janela sem roubar (tanto) o foco do mouse real.
        """
        if not WINDOWS_AVAILABLE:
            logger.warning("Clique fantasma não suportado (win32 ausente).")
            return

        try:
            l_param = win32api.MAKELONG(x_local, y_local)
            
            # 1. Simula Clique Esquerdo (Down + Up)
            win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_param)
            win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, l_param)
            time.sleep(0.1)
            
            # 2. Confirmação com Enter (Para selecionar músicas na lista)
            win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
            time.sleep(0.05)
            win32gui.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
        except Exception as e:
            logger.error(f"❌ Erro no Input Fantasma: {e}")

    @staticmethod
    def rolar_tela(direcao="down", qtd=3):
        """Simula rolagem de página (PageDown/PageUp)."""
        key = 'pgdn' if direcao == "down" else 'pgup'
        for _ in range(qtd):
            pyautogui.press(key)
            time.sleep(0.1) # Delay reduzido para ser mais ágil

    @staticmethod
    def digitar_atalho_busca(query):
        """Executa a sequência de busca: Ctrl+L -> Digita -> Enter."""
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(0.4) # Tempo para a barra de busca focar
        
        # typewrite é mais seguro para strings longas
        pyautogui.write(query, interval=0.01) 
        time.sleep(0.5) # Tempo para o Spotify carregar sugestões
        pyautogui.press('enter')

    @staticmethod
    def midia(comando):
        """
        Executa comandos de mídia mapeados.
        Suporta atalhos nativos do Spotify Desktop (Windows).
        """
        # Mapa de Comandos -> Atalhos (PyAutoGUI)
        mapa = {
            # Execução Básica
            "play_pause": "space",             # Espaço (Toggle)
            "next": ["ctrl", "right"],         # Ctrl + Seta Direita
            "prev": ["ctrl", "left"],          # Ctrl + Seta Esquerda
            "seek_fwd": ["shift", "right"],    # Avançar 10s
            "seek_back": ["shift", "left"],    # Voltar 10s
            
            # Volume
            "vol_up": ["ctrl", "up"],          # Aumentar
            "vol_down": ["ctrl", "down"],      # Diminuir
            "mute": ["ctrl", "shift", "down"], # Mute (se suportado)
            
            # Modos de Reprodução
            "shuffle": ["ctrl", "s"],          # Aleatório
            "repeat": ["ctrl", "r"],           # Repetir
            
            # Navegação
            "nav_home": ["alt", "shift", "1"],    # Home
            "nav_search": ["alt", "shift", "2"],  # Busca
            "nav_library": ["alt", "shift", "0"], # Biblioteca
            
            # Playlist / Contexto
            "like": ["ctrl", "l"],             # Curtir (Cuidado: conflita com busca se não focado na faixa)
            "new_playlist": ["ctrl", "n"]      # Nova Playlist
        }

        if comando in mapa:
            atalho = mapa[comando]
            try:
                if isinstance(atalho, list):
                    pyautogui.hotkey(*atalho)
                else:
                    pyautogui.press(atalho)
                logger.info(f"⌨️ Input enviado: {comando} -> {atalho}")
            except Exception as e:
                logger.error(f"Erro ao enviar input: {e}")
        else:
            logger.warning(f"Comando de input desconhecido: {comando}")