import time
import pyautogui
import win32gui
import win32api
import win32con

class InputManager:
    @staticmethod
    def clique_fantasma_com_enter(hwnd, x_local, y_local):
        """Seleciona (clique) e Toca (Enter)"""
        try:
            l_param = win32api.MAKELONG(x_local, y_local)
            
            # 1. Selecionar
            win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_param)
            win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, l_param)
            time.sleep(0.1)
            
            # 2. Enter
            win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
            time.sleep(0.05)
            win32gui.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
        except Exception as e:
            print(f"❌ Erro Input: {e}")

    @staticmethod
    def rolar_tela(direcao="down", qtd=3):
        key = 'pgdn' if direcao == "down" else 'pgup'
        for _ in range(qtd):
            pyautogui.press(key)
            time.sleep(0.2)

    @staticmethod
    def digitar_atalho_busca(query):
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(0.3)
        pyautogui.write(query)
        time.sleep(0.5)
        pyautogui.press('enter')

    @staticmethod
    def midia(comando):
        mapa = {
            "play_pause": "playpause",
            "next": "nexttrack",
            "prev": "prevtrack"
        }
        if comando in mapa:
            pyautogui.press(mapa[comando])