import win32gui
import win32process
import win32api
import win32con
import logging
import pyautogui
import time

logger = logging.getLogger("SPOTIFY_WINDOW")

class WindowManager:
    """
    Gerenciador de Janelas V2.6 (Anti-Fantasma).
    Garante que a janela selecionada é a UI principal do Spotify, 
    ignorando shadow windows e processos auxiliares.
    """
    
    def __init__(self):
        self.hwnd_cache = None

    def verificar_janela(self):
        """Retorna True se a janela do Spotify estiver aberta."""
        return self.obter_hwnd() is not None

    def obter_hwnd(self):
        """
        Busca o ID da janela (HWND) principal do Spotify.
        """
        self.found_hwnd = None
        
        def callback(hwnd, extra):
            # Se já achamos, para
            if self.found_hwnd: return

            # 1. Ignora janelas invisíveis para o usuário
            if not win32gui.IsWindowVisible(hwnd): return
            
            # 2. Ignora ToolWindows (Janelas de sistema/overlay que não têm barra de tarefas)
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            if style & win32con.WS_EX_TOOLWINDOW: return

            # 3. FILTRO ANTI-FANTASMA (Geometria Mínima)
            # Uma janela real do Spotify nunca será minúscula (ex: 78x25).
            try:
                rect = win32gui.GetWindowRect(hwnd)
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]
                # Se for menor que 400x400, é lixo do SO. Ignora.
                if width < 400 or height < 400: return
            except:
                return

            # 4. Pega o PID e verifica o processo
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                handle = win32api.OpenProcess(
                    win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, 
                    False, pid
                )
                exe_path = win32process.GetModuleFileNameEx(handle, 0)
                win32api.CloseHandle(handle)

                if "spotify.exe" in exe_path.lower():
                    # Achamos a verdadeira janela principal!
                    self.found_hwnd = hwnd
                    
            except Exception:
                # Fallback por título (também protegido pela geometria mínima)
                txt = win32gui.GetWindowText(hwnd).lower()
                if "spotify" in txt:
                    self.found_hwnd = hwnd

        try:
            win32gui.EnumWindows(callback, None)
        except Exception as e:
            logger.error(f"Erro ao buscar janela: {e}")
            
        return self.found_hwnd

    def obter_geometria(self):
        """Retorna (left, top, right, bottom) da janela."""
        hwnd = self.obter_hwnd()
        if hwnd:
            try:
                rect = win32gui.GetWindowRect(hwnd)
                # Dupla validação para evitar que retorne lixo se a janela foi minimizada entretanto
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]
                if width > 400 and height > 400:
                    return rect
            except: pass
        return None

    def minimizar(self):
        hwnd = self.obter_hwnd()
        if hwnd:
            try:
                win32gui.ShowWindow(hwnd, 6) # SW_MINIMIZE = 6
                logger.info("📉 Janela minimizada (Refresh UI).")
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Erro ao minimizar: {e}")

    def focar(self, hwnd=None):
        if not hwnd:
            hwnd = self.obter_hwnd()
        
        if not hwnd: return False

        try:
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, 9) # SW_RESTORE
            
            try:
                win32gui.SetForegroundWindow(hwnd)
            except Exception:
                try:
                    pyautogui.press('alt') 
                    win32gui.SetForegroundWindow(hwnd)
                except: pass
            
            for _ in range(20):
                current_focus = win32gui.GetForegroundWindow()
                if current_focus == hwnd:
                    time.sleep(0.1) 
                    return True
                time.sleep(0.1)
            
            logger.warning("⚠️ Timeout: Windows não entregou o foco para o Spotify.")
            return False

        except Exception as e:
            logger.error(f"Erro ao focar: {e}")
            return False