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
    Gerenciador de Janelas V2.5 (Determinístico).
    Garante que a janela está focada verificando o estado real do SO.
    """
    
    def __init__(self):
        self.hwnd_cache = None

    def verificar_janela(self):
        """Retorna True se a janela do Spotify estiver aberta."""
        return self.obter_hwnd() is not None

    def obter_hwnd(self):
        """
        Busca o ID da janela (HWND) verificando o processo 'spotify.exe'.
        """
        self.found_hwnd = None
        
        def callback(hwnd, extra):
            # Se já achamos, para
            if self.found_hwnd: return

            # Ignora janelas invisíveis
            if not win32gui.IsWindowVisible(hwnd): return
            
            # 1. Pega o PID (Process ID) da janela
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            try:
                # 2. Abre o processo para ler o nome do executável
                handle = win32api.OpenProcess(
                    win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, 
                    False, pid
                )
                
                # 3. Pega o caminho do arquivo (Ex: C:\Users\...\spotify.exe)
                exe_path = win32process.GetModuleFileNameEx(handle, 0)
                win32api.CloseHandle(handle)

                # 4. Verifica se é o Spotify
                if "spotify.exe" in exe_path.lower():
                    # Filtro extra: O Spotify tem várias janelas invisíveis/auxiliares.
                    # A principal geralmente tem título (mesmo que seja o nome da música) 
                    # e não é uma janela de ferramenta (ToolWindow).
                    
                    # Verifica estilo da janela para evitar overlays vazios
                    style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                    if style & win32con.WS_VISIBLE:
                        # Achamos!
                        self.found_hwnd = hwnd
                        
            except Exception:
                # Se não conseguir ler o processo (permissão), tenta fallback por título
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
                return rect
            except: pass
        return None

    def minimizar(self):
        """
        Minimiza a janela para forçar refresh gráfico.
        Útil quando a interface do Spotify trava ou elementos não são renderizados.
        """
        hwnd = self.obter_hwnd()
        if hwnd:
            try:
                win32gui.ShowWindow(hwnd, 6) # SW_MINIMIZE = 6
                logger.info("📉 Janela minimizada (Refresh UI).")
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Erro ao minimizar: {e}")

    def focar(self, hwnd=None):
        """
        Traz a janela para frente com VALIDAÇÃO REAL.
        Não retorna até ter certeza que o foco mudou (ou dar timeout).
        """
        if not hwnd:
            hwnd = self.obter_hwnd()
        
        if not hwnd: return False

        try:
            # 1. Se estiver minimizada, restaura
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, 9) # SW_RESTORE
            
            # 2. Tenta focar (Primeira Tentativa)
            try:
                win32gui.SetForegroundWindow(hwnd)
            except Exception:
                # Truque do Alt para "roubar" foco no Windows 10/11 se estiver bloqueado
                try:
                    pyautogui.press('alt') 
                    win32gui.SetForegroundWindow(hwnd)
                except: pass
            
            # 3. LOOP DE GARANTIA (Determinístico)
            # Espera até 2 segundos para o Windows processar a troca de contexto
            for _ in range(20):
                current_focus = win32gui.GetForegroundWindow()
                if current_focus == hwnd:
                    # Pequeno buffer para o render (GPU) alcançar a lógica (CPU)
                    time.sleep(0.1) 
                    return True
                time.sleep(0.1)
            
            logger.warning("⚠️ Timeout: Windows não entregou o foco para o Spotify.")
            return False

        except Exception as e:
            logger.error(f"Erro ao focar: {e}")
            return False