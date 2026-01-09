import time
import webbrowser
import pyautogui
import json
import re
import urllib.parse
import os
import pygetwindow as gw
from .base_agente import AgenteEspecialista

try:
    from jarvis_system.cortex_frontal.brain_llm import llm
except ImportError:
    llm = None

# ==============================================================================
# CAMADA 1: NLU (Agora com Inteligência Real)
# ==============================================================================
class SpotifyNLU:
    def analisar(self, comando: str) -> dict:
        # Atalhos rápidos locais (para não gastar token com coisas óbvias)
        comando_lower = comando.lower()
        if comando_lower in ["voltar a tocar", "continue", "resume", "solta o som", "play"]:
            return {"intent": "RESUME"}
        
        if any(w in comando_lower for w in ["pausa", "pare", "stop", "silencio", "parar"]):
            return {"intent": "PAUSE"}

        # Se não é comando simples, DELEGAMOS AO CÉREBRO (Groq)
        if not llm: return self._fallback_busca(comando)

        # --- O NOVO PROMPT CORRETOR ---
        prompt = f"""
        Você é um especialista em música e API do Spotify.
        Analise o comando de voz do usuário, que pode conter erros fonéticos.

        INPUT DO USUÁRIO: "{comando}"

        SUA MISSÃO:
        1. Identifique a intenção: PLAY_SEARCH (buscar), RESUME, PAUSE, NEXT, PREVIOUS.
        2. CORRIJA nomes de artistas/músicas. Ex: "Frigilson" -> "Frei Gilson", "Nirvava" -> "Nirvana", "30 pra 1" -> "30PRAUM".
        3. Retorne APENAS o JSON.

        JSON OUTPUT FORMAT:
        {{
            "intent": "PLAY_SEARCH",
            "query": "Nome Corrigido do Artista/Musica"
        }}
        """
        try:
            # Temperatura 0.1 para ele ser "criativo" na correção mas preciso no JSON
            resposta = llm.pensar(prompt).strip()
            
            # Extrai JSON caso o LLM fale algo antes
            match = re.search(r'\{.*\}', resposta, re.DOTALL)
            if match: 
                dados = json.loads(match.group())
                print(f"[NLU] Correção LLM: '{comando}' -> '{dados.get('query')}'")
                return dados
        except Exception as e:
            print(f"[Erro NLU] {e}")
        
        return self._fallback_busca(comando)

    def _fallback_busca(self, comando: str) -> dict:
        termo = comando.replace("tocar", "").replace("spotify", "").strip()
        if not termo: return {"intent": "RESUME"}
        return {"intent": "PLAY_SEARCH", "query": termo}

# ==============================================================================
# CAMADA 2: CONTROLLER (Com Foco Forçado)
# ==============================================================================
class SpotifyController:
    def __init__(self):
        self.base_dir = os.getcwd()
        self.img_play = os.path.join(self.base_dir, "img", "play_spotify.png")

    def _forcar_foco_janela(self):
        """
        Truque para burlar a proteção de foco do Windows.
        Se a janela estiver escondida, ele minimiza e restaura para forçar o topo.
        """
        try:
            janelas = gw.getWindowsWithTitle('Spotify')
            validas = [w for w in janelas if "Spotify" in w.title] # Filtro mais robusto
            
            if validas:
                win = validas[0]
                
                # Se já estiver ativa, não faz nada (evita piscar a tela)
                if win.isActive:
                    return win

                print(f"[Janela] Forçando foco em: {win.title}")
                
                # O Truque do Windows:
                if win.isMinimized:
                    win.restore()
                else:
                    # Minimizar e Restaurar força o Z-Order (traz para frente de tudo)
                    win.minimize()
                    time.sleep(0.1)
                    win.restore()
                
                win.activate()
                time.sleep(0.5) # Tempo para a animação do Windows terminar
                return win
        except Exception as e:
            print(f"[Erro Janela] {e}")
        return None

    def _clicar_botao_verde(self, win):
        print("[Visual] Buscando botão verde...")
        try:
            start = time.time()
            # Procura por 4 segundos (aumentei o tempo pois a janela pode estar animando)
            while time.time() - start < 4.0:
                # grayscale=False é importante pois o botão é VERDE característico
                botoes = list(pyautogui.locateAllOnScreen(self.img_play, confidence=0.8, grayscale=False))
                
                for btn in botoes:
                    cy = btn.top + (btn.height / 2)
                    # Filtra botão do rodapé (Player) - ignora os 15% inferiores
                    if cy < (win.top + win.height * 0.85):
                        centro = pyautogui.center(btn)
                        print(f"[Visual] ✨ ACHEI! Clicando em {centro}")
                        pyautogui.click(centro.x, centro.y)
                        return True
                time.sleep(0.3)
        except Exception as e:
            print(f"[Visual Falhou] {e}") # Não cracha, apenas avisa
        
        return False

    def play_search(self, query: str):
        print(f"[Controller] Buscando: {query}")
        
        # 1. Abre via Link (Isso geralmente já foca o app)
        link = f"spotify:search:{urllib.parse.quote(query)}"
        webbrowser.open(link)
        time.sleep(3.0) 
        
        # 2. Garante que está VISÍVEL (Foco Forçado)
        win = self._forcar_foco_janela()
        if not win: 
            print("[Erro] Não encontrei a janela do Spotify.")
            return

        # 3. Visão Computacional
        if os.path.exists(self.img_play):
            if self._clicar_botao_verde(win): return
        else:
            print(f"[Aviso] Imagem {self.img_play} não existe.")

        # 4. Fallback (Navegação Cega)
        print("[Navegação] Modo Cego: Tab+Enter.")
        
        # Clica no centro para garantir foco do input
        pyautogui.click(win.left + win.width//2, win.top + win.height//3)
        time.sleep(0.2)
        
        pyautogui.press('tab')
        time.sleep(0.1)
        pyautogui.press('enter') 

    def resume(self):
        self._forcar_foco_janela()
        pyautogui.press('space') 

    def pause(self):
        self._forcar_foco_janela()
        pyautogui.press('space')

    def next_track(self):
        self._forcar_foco_janela()
        pyautogui.hotkey('ctrl', 'right')

    def previous_track(self):
        self._forcar_foco_janela()
        pyautogui.hotkey('ctrl', 'left')

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
        return ["spotify", "tocar", "ouvir", "play", "som", "musica", "pausa", "pare", "stop", "silencio", "voltar"]

    def executar(self, comando: str, **kwargs) -> str:
        dados = self.nlu.analisar(comando)
        intencao = dados.get("intent")
        query = dados.get("query", "")
        
        if intencao == "PLAY_SEARCH":
            self.controller.play_search(query)
            return f"Buscando {query}."
        elif intencao == "RESUME":
            self.controller.resume()
            return "Ok."
        elif intencao == "PAUSE":
            self.controller.pause()
            return "Pausado."
        elif intencao == "NEXT":
            self.controller.next_track()
            return "Próxima."
        elif intencao == "PREVIOUS":
            self.controller.previous_track()
            return "Anterior."
            
        return "Comando não entendido."