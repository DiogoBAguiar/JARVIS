import logging
import time
import pyautogui
import pyperclip
from .background import BackgroundInputHandler
from .keyboard import KeyboardMacroHandler

logger = logging.getLogger("SPOTIFY_INPUT")

class InputManager:
    """
    Fachada (Facade) para gerenciamento de entradas.
    Unifica interações de baixo nível (Win32) e alto nível (PyAutoGUI).
    """

    def __init__(self):
        # Configurações globais de segurança
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        # Composição: Instancia os especialistas se eles existirem
        # (Usamos try/except caso você ainda não tenha criado esses arquivos, para não quebrar tudo)
        try:
            self.bg_handler = BackgroundInputHandler()
            self.kb_handler = KeyboardMacroHandler()
        except Exception as e:
            logger.warning(f"Handlers auxiliares não carregados (usando apenas input básico): {e}")
            self.bg_handler = None
            self.kb_handler = None

    def buscar(self, termo: str):
        """
        Realiza a busca robusta (Ctrl+L -> Limpar -> Colar -> Enter).
        """
        logger.info(f"⌨️  [InputManager] Buscando: '{termo}'")
        
        # 1. Atalho Ctrl+L (Foca na busca)
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(0.5)
        
        # 2. Garante campo limpo (Ctrl+A -> Backspace)
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        pyautogui.press('backspace')
        
        # 3. Digita (Usa Clipboard para evitar erros de acentuação)
        try:
            pyperclip.copy(termo)
            pyautogui.hotkey('ctrl', 'v')
        except Exception:
            # Fallback se clipboard falhar
            pyautogui.write(termo, interval=0.05)
            
        time.sleep(1.5) # Aumentei um pouco para garantir que o Spotify processe
        
        # 4. Confirma
        pyautogui.press('enter')
        time.sleep(0.5)
        
        # Tira o mouse do caminho (Centro da tela)
        sw, sh = pyautogui.size()
        pyautogui.moveTo(sw/2, sh/2)

    # --- Métodos de Delegação (Mantendo compatibilidade) ---

    def clique_fantasma_com_enter(self, hwnd, x_local, y_local):
        if self.bg_handler:
            return self.bg_handler.clique_fantasma_com_enter(hwnd, x_local, y_local)
        return False

    def rolar_tela(self, direcao="down", qtd=3):
        if self.kb_handler:
            self.kb_handler.rolar_pagina(direcao, qtd)
        else:
            # Fallback simples
            if direcao == "down": pyautogui.scroll(-100 * qtd)
            else: pyautogui.scroll(100 * qtd)

    def digitar_atalho_busca(self, query: str):
        # Redireciona para o novo método robusto
        self.buscar(query)

    def midia(self, comando: str):
        if self.kb_handler:
            self.kb_handler.executar_comando_midia(comando)
        else:
            # Fallback teclas multimidia
            if comando == "play_pause": pyautogui.press("playpause")
            elif comando == "next": pyautogui.press("nexttrack")
            elif comando == "prev": pyautogui.press("prevtrack")