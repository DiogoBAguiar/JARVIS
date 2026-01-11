import os
import sys
import time
import re
import json
import warnings

from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By

# --- INTEGRAÇÃO GEMINI ---
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Configuração de Ambiente
load_dotenv()
warnings.filterwarnings("ignore")

# Ajuste de path para garantir importações relativas se necessário
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '../../..'))

from jarvis_system.hipocampo.memoria import memoria
from jarvis_system.cortex_frontal.observability import JarvisLogger

log = JarvisLogger("SPOTIFY_INGESTOR")

# --- CONFIGURAÇÃO DA IA ---
API_KEY = os.getenv("GEMINI_API_KEY")
client = None
if API_KEY:
    try:
        client = genai.Client(api_key=API_KEY)
    except Exception as e:
        log.warning(f"Erro ao iniciar Gemini: {e}")

class SpotifyIngestor:
    def __init__(self):
        self.driver = None

    def _conectar_edge_debug(self):
        """Conecta ao Edge que já está aberto na porta 9222."""
        options = Options()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        
        # Tenta localizar o driver no diretório atual ou no path
        base_dir = os.getcwd()
        driver_local = os.path.join(base_dir, "msedgedriver.exe")
        service = Service(driver_local) if os.path.exists(driver_local) else Service()
        
        self.driver = webdriver.Edge(service=service, options=options)
        return self.driver

    def _limpar_texto(self, texto_bruto):
        if not texto_bruto: return None, None
        linhas = [l.strip() for l in texto_bruto.split('\n') if l.strip()]
        lixo_exato = ["E", "Explicit", "Lyrics", "Letra", "Tocando", "Playing", "Ao vivo", "Live", "Video"]
        
        limpo = []
        for l in linhas:
            if re.match(r'^\d+$', l): continue
            if re.match(r'^\d+:\d+$', l): continue
            if l in lixo_exato: continue
            l_limpa = re.sub(r'^E\s+', '', l) 
            limpo.append(l_limpa)
        
        if len(limpo) < 2: return None, None
        return limpo[0], limpo[1] # Música, Artista

    def _consultar_gemini_info(self, musica, artista):
        if not client: return {"genero": "Música", "album": "Desconhecido"}

        prompt = f"""
        Analyze this song: "{musica}" by "{artista}".
        Return a JSON with:
        1. "genero": The specific music genre (e.g., "Católica", "Sertanejo", "Rock", "Worship", "Trap").
        2. "album": The most likely album name (or "Single").
        STRICT JSON OUTPUT ONLY: {{ "genero": "...", "album": "..." }}
        """
        
        try:
            response = client.models.generate_content(
                model="gemma-2-9b-it", # Ajuste conforme seu modelo disponível
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.1)
            )
            texto = response.text.replace("```json", "").replace("```", "").strip()
            inicio = texto.find("{")
            fim = texto.rfind("}") + 1
            if inicio != -1 and fim != -1:
                return json.loads(texto[inicio:fim])
        except Exception:
            pass
        return {"genero": "Música", "album": "Desconhecido"}

    def _scroll_focado_no_centro(self):
        try:
            self.driver.execute_script("""
                var x = window.innerWidth / 2;
                var y = window.innerHeight / 2;
                var elemento = document.elementFromPoint(x, y);
                while (elemento) {
                    const style = window.getComputedStyle(elemento);
                    if (style.overflowY === 'scroll' || style.overflowY === 'auto' || style.overflowY === 'overlay') {
                        elemento.scrollBy(0, 700); return;
                    }
                    elemento = elemento.parentElement;
                }
                window.scrollBy(0, 700);
            """)
        except: pass

    def processar_extracao(self, mode="likes", playlist_name=None):
        """
        Método público para iniciar a extração.
        mode: 'likes' ou 'playlist'
        """
        try:
            self._conectar_edge_debug()
            if not self.driver:
                log.error("Não foi possível conectar ao Edge.")
                return 0

            contexto_tag = "spotify_likes"
            
            if mode == "likes":
                self.driver.get("https://open.spotify.com/collection/tracks") # Hack de foco
                time.sleep(2)
            elif mode == "playlist" and playlist_name:
                contexto_tag = f"playlist_{playlist_name}"
                print(f"👉 Por favor, navegue até a playlist '{playlist_name}' manualmente agora.")
                time.sleep(5) # Tempo para o usuário reagir se for automático, ou ajustável

            log.info(f"📜 Iniciando extração: {contexto_tag}")
            
            coletados = set()
            tentativas_sem_novidade = 0
            total_processado = 0
            
            while True:
                elementos = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="tracklist-row"]')
                novos_nesta_tela = 0
                
                for el in elementos:
                    try:
                        musica, artista = self._limpar_texto(el.text)
                        if not musica or not artista: continue
                        
                        chave = f"{musica}|{artista}"
                        if chave not in coletados:
                            coletados.add(chave)
                            novos_nesta_tela += 1
                            total_processado += 1
                            
                            print(f"\r🤖 Consultando IA: {musica[:15]}...", end="")
                            info_ia = self._consultar_gemini_info(musica, artista)
                            
                            dados_extras = {
                                "explicit": " (E)" in el.text,
                                "album": info_ia.get("album", "Single"),
                                "genero": info_ia.get("genero", "Música")
                            }
                            
                            memoria.memorizar_musica(
                                musica=musica, 
                                artista=artista, 
                                tags=contexto_tag,
                                extra_info=dados_extras
                            )
                            print(f"\r📥 [{total_processado}] {musica[:20]} | {dados_extras['genero']}")
                            time.sleep(0.5) 
                    except: continue

                self._scroll_focado_no_centro()
                time.sleep(1.2) 
                
                if novos_nesta_tela == 0:
                    tentativas_sem_novidade += 1
                    print(".", end="", flush=True) 
                    if tentativas_sem_novidade >= 8:
                        break
                else:
                    tentativas_sem_novidade = 0
            
            print(f"\n🏁 Processo concluído. {total_processado} itens.")
            return total_processado

        except Exception as e:
            log.critical(f"Erro no Ingestor: {e}")
            return 0