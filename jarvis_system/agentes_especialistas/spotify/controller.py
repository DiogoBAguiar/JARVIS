import time
import win32gui
import pyautogui
import subprocess # <--- Importante para abrir o aplicativo
from .window import WindowManager
from .input import InputManager
from .vision import VisionSystem

class SpotifyController:
    def __init__(self):
        self.window = WindowManager()
        self.input = InputManager()
        self.vision = VisionSystem()

    def launch_app(self):
        """
        Abre o Spotify usando o protocolo nativo do Windows.
        Isso funciona independente de onde o usuário instalou o Spotify.
        """
        print("🚀 [Controller] Inicializando Spotify...")
        try:
            # O comando 'start spotify:' diz ao Windows para abrir o app associado a esse protocolo
            subprocess.run("start spotify:", shell=True)
            
            # Damos um tempo para a janela subir e renderizar
            print("⏳ Aguardando carregamento...")
            time.sleep(3) 
            
            # Força o foco na janela recém-aberta
            if self._preparar_janela():
                return True
            return False
        except Exception as e:
            print(f"❌ Erro ao abrir Spotify: {e}")
            return False

    def _preparar_janela(self):
        """Garante que a janela está focada e retorna o HWND."""
        hwnd = self.window.obter_hwnd()
        if hwnd: self.window.focar(hwnd)
        return hwnd

    def _obter_regiao_janela(self, hwnd):
        """
        Calcula a geometria da janela (x, y, largura, altura).
        Isso permite que o OCR leia APENAS a janela do Spotify, não a tela toda.
        """
        if not hwnd: return None
        try:
            rect = win32gui.GetWindowRect(hwnd) # Retorna (left, top, right, bottom)
            w = rect[2] - rect[0]
            h = rect[3] - rect[1]
            return (rect[0], rect[1], w, h) # Formato que o PyAutoGUI/EasyOCR esperam
        except:
            return None

    def buscar_e_clicar(self, texto_alvo, tentar_rolagem=True):
        hwnd = self._preparar_janela()
        if not hwnd: return False
        
        # 1. Pega a área da janela para otimizar o OCR
        regiao = self._obter_regiao_janela(hwnd)
        
        print(f"🕵️ [Controller] Buscando (Inteligente): '{texto_alvo}'")
        max_tentativas = 3 if tentar_rolagem else 1

        for _ in range(max_tentativas):
            # 2. Usa a nova BUSCA FUZZY (aceita erros de leitura)
            # Passamos a 'region' para ser ultra-rápido
            coords_tela = self.vision.encontrar_texto_fuzzy(texto_alvo, region=regiao)
            
            if coords_tela:
                cx, cy = coords_tela
                
                # 3. Converte Global (Tela) -> Local (Janela)
                pl = win32gui.ScreenToClient(hwnd, (cx, cy))
                
                # 4. Clica e confirma com Enter
                self.input.clique_fantasma_com_enter(hwnd, pl[0], pl[1])
                return True
            
            if tentar_rolagem:
                self.input.rolar_tela("down", 1)
                # Atualiza a região caso a janela tenha movido (raro, mas possível)
                regiao = self._obter_regiao_janela(hwnd)
        
        return False

    def play_search(self, query):
        hwnd = self._preparar_janela()
        self.input.digitar_atalho_busca(query)
        print("⏳ Aguardando resultados...")
        time.sleep(2.5) # Tempo para o Spotify renderizar

        # Otimização: Busca visual restrita à janela
        regiao = self._obter_regiao_janela(hwnd)

        # 1. Tenta Botão Play Visual (Botão Verde)
        # Agora passamos 'region' para o locateOnScreen ser instantâneo
        botao = self.vision.procurar_botao_play(region=regiao)
        
        if botao:
            centro = pyautogui.center(botao)
            pl = win32gui.ScreenToClient(hwnd, (centro.x, centro.y))
            self.input.clique_fantasma_com_enter(hwnd, pl[0], pl[1])
            return

        # 2. Tenta Texto da Música (Fuzzy Logic)
        # Se falhar a imagem, procura pelo texto aproximado do que digitamos
        print("⚠️ Botão verde não visto. Tentando achar o texto da música...")
        if self.buscar_e_clicar(query, tentar_rolagem=False):
            return

        # 3. Fallback Teclado (Último recurso)
        print("⌨️ Modo cego (Teclado)...")
        pyautogui.press('tab')
        pyautogui.press('enter')

    # Métodos Proxy para o Agente usar
    def resume(self): self.input.midia("play_pause")
    def pause(self): self.input.midia("play_pause")
    def next_track(self): self.input.midia("next")
    def previous_track(self): self.input.midia("prev")
    def scroll(self, direction): self.input.rolar_tela(direction)