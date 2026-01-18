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
        Usa SendMessage para garantir que o clique foi processado antes do Enter.
        """
        if not WINDOWS_AVAILABLE:
            logger.warning("Tentativa de clique fantasma falhou: Win32 indisponível.")
            return False

        try:
            l_param = win32api.MAKELONG(int(x_local), int(y_local))
            
            # --- ATUALIZAÇÃO CRÍTICA (Sincronia) ---
            # 1. Simula Clique Esquerdo (Down + Up)
            # Usamos SendMessage em vez de PostMessage.
            # O código vai PARAR nestas linhas até o Spotify processar o clique.
            win32gui.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_param)
            win32gui.SendMessage(hwnd, win32con.WM_LBUTTONUP, 0, l_param)
            
            # Pausa de segurança para a UI do Spotify renderizar a seleção (Highlight)
            time.sleep(0.05)
            
            # 2. Confirmação com Enter (Para selecionar músicas na lista)
            # O clique já foi garantido acima, então o Enter agora vai no alvo certo.
            win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
            time.sleep(0.05)
            win32gui.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
            
            return True
        except Exception as e:
            logger.error(f"❌ Erro no Input Fantasma: {e}")
            return False