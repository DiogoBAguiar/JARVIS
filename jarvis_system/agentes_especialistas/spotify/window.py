import time
import win32gui
import win32con

class WindowManager:
    @staticmethod
    def obter_hwnd():
        hwnd = win32gui.FindWindow(None, "Spotify Premium")
        if not hwnd: hwnd = win32gui.FindWindow("Chrome_WidgetWin_0", "Spotify Free")
        
        # Busca genérica
        if not hwnd:
            def callback(h, l):
                if "Spotify" in win32gui.GetWindowText(h): l.append(h)
            l = []
            win32gui.EnumWindows(callback, l)
            if l: hwnd = l[0]
        return hwnd

    @staticmethod
    def focar(hwnd):
        if hwnd:
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            try:
                win32gui.SetForegroundWindow(hwnd)
            except: pass
            time.sleep(0.5)