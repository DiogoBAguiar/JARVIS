import time
import logging
import pyautogui # <--- ADICIONADO: Necessário para o truque de foco

logger = logging.getLogger("WINDOW_DRIVER")

# Importação Segura
try:
    import win32gui
    import win32con
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False
    logger.warning("Bibliotecas win32 ausentes. Gestão de janelas desativada.")
    # Mocks para evitar NameError
    win32gui = None
    win32con = None

class Win32WindowDriver:
    """
    Wrapper de baixo nível para a API do Windows (win32gui).
    Isola a complexidade técnica do resto do sistema.
    """

    def find_exact(self, window_name: str):
        """Busca janela por título exato."""
        if not WINDOWS_AVAILABLE: return None
        try:
            hwnd = win32gui.FindWindow(None, window_name)
            # FindWindow retorna 0 se não achar
            return hwnd if hwnd > 0 else None
        except Exception:
            return None

    def find_by_class(self, class_name: str, window_name: str):
        """Busca por Classe e Título (Mais específico)."""
        if not WINDOWS_AVAILABLE: return None
        try:
            hwnd = win32gui.FindWindow(class_name, window_name)
            return hwnd if hwnd > 0 else None
        except Exception:
            return None

    def find_partial_text(self, text_segment: str):
        """
        Busca varrendo todas as janelas abertas por um trecho de texto.
        Custo computacional um pouco maior, usar como fallback.
        """
        if not WINDOWS_AVAILABLE: return None
        
        found_hwnd = []

        def callback(hwnd, ctx):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if text_segment in title:
                    ctx.append(hwnd)

        try:
            win32gui.EnumWindows(callback, found_hwnd)
            return found_hwnd[0] if found_hwnd else None
        except Exception as e:
            logger.error(f"Erro ao enumerar janelas: {e}")
            return None

    def force_focus(self, hwnd):
        """
        Traz a janela para frente com VALIDAÇÃO REAL (Determinística).
        """
        if not WINDOWS_AVAILABLE or not hwnd: return False

        try:
            # 1. Se estiver minimizada (Iconic), restaura
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            
            # 2. Tenta focar (Tentativa Padrão)
            try:
                win32gui.SetForegroundWindow(hwnd)
            except Exception:
                # 3. Fallback: Truque do Alt para Windows 10/11 teimosos
                try:
                    pyautogui.press('alt')
                    win32gui.SetForegroundWindow(hwnd)
                except: pass
                
            # 4. LOOP DE GARANTIA (Determinístico)
            # Verifica se o foco realmente mudou antes de retornar
            for _ in range(20): # Tenta por até 2 segundos
                if win32gui.GetForegroundWindow() == hwnd:
                    time.sleep(0.05) # Buffer para renderização
                    return True
                time.sleep(0.1)

            logger.warning(f"Timeout: Não foi possível focar a janela HWND {hwnd}")
            return False

        except Exception as e:
            logger.error(f"Erro ao focar janela {hwnd}: {e}")
            return False

    def get_window_rect(self, hwnd):
        """
        Retorna as coordenadas da janela (left, top, right, bottom).
        Essencial para suportar múltiplos monitores e resoluções variadas.
        """
        if not WINDOWS_AVAILABLE or not hwnd: return None
        try:
            # Retorna uma tupla (esquerda, topo, direita, baixo)
            rect = win32gui.GetWindowRect(hwnd)
            return rect
        except Exception as e:
            logger.error(f"Erro ao ler geometria da janela: {e}")
            return None