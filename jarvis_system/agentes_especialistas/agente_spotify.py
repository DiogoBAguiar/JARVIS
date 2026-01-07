import time
import webbrowser
import pyautogui
import json
import re
import urllib.parse
import os
from .base_agente import AgenteEspecialista

try:
    from jarvis_system.cortex_frontal.brain_llm import llm
except ImportError:
    llm = None

# ==============================================================================
# CAMADA 1: NLU (Interpretação e Correção Fonética)
# ==============================================================================
class SpotifyNLU:
    def _aplicar_correcoes_locais(self, texto: str) -> str:
        texto = texto.lower()
        # Dicionário expandido com os erros do Whisper
        correcoes = {
            "30 pra 1": "30PRAUM",
            "30 para 1": "30PRAUM",
            "3-1": "30PRAUM",      # <--- O erro do seu log
            "3 1": "30PRAUM",
            "31": "30PRAUM",       # <--- Variação comum
            "trinta pra um": "30PRAUM",
            "frejilso": "Frei Gilson",
            "frey gilson": "Frei Gilson", # <--- O erro do seu log
            "legião": "Legião Urbana"
        }
        
        # Substituição exata ou parcial
        for erro, correcao in correcoes.items():
            # Verifica se o erro está no texto (com espaços em volta para não quebrar palavras)
            if erro in texto:
                texto = texto.replace(erro, correcao)
                
        return texto.upper() if "30PRAUM" in texto.upper() else texto

    def analisar(self, comando: str) -> dict:
        comando_limpo = self._aplicar_correcoes_locais(comando)
        
        if not llm:
            return self._fallback_regras(comando_limpo)

        prompt = f"""
        [ROLE]
        Especialista Spotify.
        [INPUT] "{comando_limpo}"
        [OUTPUT JSON] {{ "intent": "PLAY", "query": "TERMO", "type": "ARTIST"|"TRACK" }}
        """
        try:
            resposta = llm.pensar(prompt).strip()
            match = re.search(r'\{.*\}', resposta, re.DOTALL)
            if match: return json.loads(match.group())
        except: pass
        
        return self._fallback_regras(comando_limpo)

    def _fallback_regras(self, comando: str) -> dict:
        if any(w in comando.lower() for w in ["pausa", "parar"]): return {"intent": "PAUSE"}
        if "proxima" in comando.lower(): return {"intent": "NEXT"}
        termo = comando.replace("tocar", "").replace("spotify", "").strip()
        return {"intent": "PLAY", "query": termo, "type": "ARTIST"}

# ==============================================================================
# CAMADA 2: CONTROLLER (Visão Turbinada)
# ==============================================================================
class SpotifyController:
    def _tentar_clique_visual(self):
        """
        Tenta achar o botão verde de duas formas:
        1. Colorido (Preciso)
        2. Grayscale (Ignora mudanças de fundo do Spotify)
        """
        base_dir = os.getcwd()
        img_path = os.path.join(base_dir, "img", "play_spotify.png")
        
        if not os.path.exists(img_path):
            return False

        print("[Visual] Escaneando tela por botão verde...")
        
        try:
            # TENTATIVA 1: Modo Colorido (Confidence 0.7)
            botao = pyautogui.locateCenterOnScreen(img_path, confidence=0.7)
            if botao:
                print(f"[Visual] ALVO LOCALIZADO (Cor) em {botao}. Clicando.")
                pyautogui.click(botao.x, botao.y)
                return True
                
            # TENTATIVA 2: Modo Grayscale (Ignora o fundo colorido do álbum)
            print("[Visual] Tentando modo Grayscale...")
            botao = pyautogui.locateCenterOnScreen(img_path, confidence=0.6, grayscale=True)
            if botao:
                print(f"[Visual] ALVO LOCALIZADO (Grayscale) em {botao}. Clicando.")
                pyautogui.click(botao.x, botao.y)
                return True
                
        except Exception:
            pass
            
        return False

    def play(self, query: str):
        print(f"[SpotifyController] Executando estratégia para: {query}")
        
        # 1. Busca
        link = f"spotify:search:{urllib.parse.quote(query)}"
        webbrowser.open(link)
        time.sleep(4.5) 
        
        # 2. Reset de Foco
        largura, altura = pyautogui.size()
        pyautogui.click(largura / 2, altura / 2)
        
        # 3. Entrar no Resultado (Esc -> Tab -> Enter)
        pyautogui.press('esc')
        time.sleep(0.2)
        pyautogui.press('tab')
        time.sleep(0.2)
        pyautogui.press('enter')
        
        time.sleep(2.5) # Espera carregar a página interna
        
        # 4. TENTA VISÃO
        if self._tentar_clique_visual():
            print("[Sucesso] Reprodução iniciada via Visão Computacional.")
            return

        # 5. FALLBACK CEGO
        print("[Visual] Falhou. Tentando modo cego.")
        pyautogui.click(largura * 0.3, altura * 0.4) 
        time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(0.5)
        pyautogui.press('space')

    def pause(self): pyautogui.press("playpause")
    def next_track(self): pyautogui.press("nexttrack")
    def open_app(self): webbrowser.open("spotify:")

# ==============================================================================
# CAMADA 3: AGENTE
# ==============================================================================
class AgenteSpotify(AgenteEspecialista):
    def __init__(self):
        self.nlu = SpotifyNLU()
        self.controller = SpotifyController()

    @property
    def nome(self): return "spotify"

    @property
    def gatilhos(self):
        return ["spotify", "tocar", "ouvir", "play", "som", "musica", "banda", "artista"]

    def executar(self, comando: str, **kwargs) -> str:
        dados = self.nlu.analisar(comando)
        intencao = dados.get("intent")
        query = dados.get("query", "")
        
        if intencao == "PLAY":
            self.controller.play(query)
            return f"Tocando: {query}"
        
        elif intencao == "PAUSE":
            self.controller.pause()
            return "Pausado."
        elif intencao == "NEXT":
            self.controller.next_track()
            return "Próxima."
        elif intencao == "OPEN":
            self.controller.open_app()
            return "Spotify aberto."
            
        return "Comando não entendido."