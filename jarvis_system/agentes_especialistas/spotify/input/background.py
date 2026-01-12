import time
import logging

# Configuração de Logs
logger = logging.getLogger("INPUT_BACKGROUND")

# Tentativa de Importação Segura
try:
    import win32gui
    import win32api
    import win32con
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False
    logger.warning("Bibliotecas win32 ausentes. Cliques em background desativados.")

class BackgroundInputHandler:
    """
    Responsável por interações de baixo nível (API do Windows).
    Permite enviar comandos para janelas sem mover o mouse físico.
    """

    def clique_fantasma_com_enter(self, hwnd, x_local, y_local):
        """
        Envia mensagem de clique diretamente para a fila de eventos da janela.
        """
        if not WINDOWS_AVAILABLE:
            logger.warning("Tentativa de clique fantasma falhou: Win32 indisponível.")
            return False

        try:
            l_param = win32api.MAKELONG(int(x_local), int(y_local))
            
            # 1. Simula Clique Esquerdo (Down + Up)
            win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_param)
            win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, l_param)
            time.sleep(0.1)
            
            # 2. Confirmação com Enter (Para selecionar músicas na lista)
            win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
            time.sleep(0.05)
            win32gui.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
            
            return True
        except Exception as e:
            logger.error(f"❌ Erro no Input Fantasma: {e}")
            return False