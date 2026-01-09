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
sys.path.append(os.getcwd())
warnings.filterwarnings("ignore")

from jarvis_system.hipocampo.memoria import memoria
from jarvis_system.cortex_frontal.observability import JarvisLogger

log = JarvisLogger("SPOTIFY_V3_INTELLIGENT")

# --- CONFIGURAÇÃO DA IA ---
API_KEY = os.getenv("GEMINI_API_KEY")
client = None
if API_KEY:
    client = genai.Client(api_key=API_KEY)
else:
    log.warning("⚠️ Chave GEMINI_API_KEY não encontrada. O enriquecimento será pulado.")

def conectar_edge_debug():
    """Conecta ao Edge que já está aberto na porta 9222."""
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    base_dir = os.getcwd()
    driver_local = os.path.join(base_dir, "msedgedriver.exe")
    service = Service(driver_local) if os.path.exists(driver_local) else Service()
    
    return webdriver.Edge(service=service, options=options)

def limpar_texto(texto_bruto):
    if not texto_bruto: return None, None
    linhas = [l.strip() for l in texto_bruto.split('\n') if l.strip()]
    lixo_exato = ["E", "Explicit", "Lyrics", "Letra", "Tocando", "Playing", "Ao vivo", "Live", "Video"]
    
    limpo = []
    for l in linhas:
        if re.match(r'^\d+$', l): continue
        if re.match(r'^\d+:\d+$', l): continue
        if l in lixo_exato: continue
        l_limpa = re.sub(r'^E\s+', '', l) # Remove "E " (Explicit)
        limpo.append(l_limpa)
    
    if len(limpo) < 2: return None, None
    return limpo[0], limpo[1] # Música, Artista

def consultar_gemini_info(musica, artista):
    """
    Pergunta ao Gemini detalhes sobre a música para preencher metadados.
    """
    if not client: return {}

    prompt = f"""
    Analyze this song: "{musica}" by "{artista}".
    Return a JSON with:
    1. "genero": The specific music genre (e.g., "Católica", "Sertanejo", "Rock", "Worship", "Trap").
    2. "album": The most likely album name (or "Single").
    
    Context: If artist is "Frei Gilson", genre is likely "Católica/Worship".
    
    STRICT JSON OUTPUT ONLY: {{ "genero": "...", "album": "..." }}
    """
    
    try:
        # Usando gemma-3-27b-it que tem cota alta e é rápido
        response = client.models.generate_content(
            model="gemma-3-27b-it",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.1)
        )
        
        texto = response.text.replace("```json", "").replace("```", "").strip()
        # Tenta extrair JSON caso haja texto em volta
        inicio = texto.find("{")
        fim = texto.rfind("}") + 1
        if inicio != -1 and fim != -1:
            return json.loads(texto[inicio:fim])
            
    except Exception as e:
        # Silencia erros de API para não travar o scraper
        pass
    
    return {"genero": "Música", "album": "Desconhecido"}

def scroll_focado_no_centro(driver):
    try:
        driver.execute_script("""
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

def extrair_playlist(driver, contexto_tag="spotify_likes"):
    log.info(f"📜 Iniciando extração INTELIGENTE: {contexto_tag}")
    
    coletados = set()
    tentativas_sem_novidade = 0
    total_processado = 0
    
    time.sleep(1)

    while True:
        elementos = driver.find_elements(By.CSS_SELECTOR, '[data-testid="tracklist-row"]')
        novos_nesta_tela = 0
        
        for el in elementos:
            try:
                musica, artista = limpar_texto(el.text)
                
                if not musica or not artista: continue
                
                chave = f"{musica}|{artista}"
                
                if chave not in coletados:
                    coletados.add(chave)
                    novos_nesta_tela += 1
                    total_processado += 1
                    
                    # 🧠 O PULO DO GATO: Enriquecimento via IA
                    print(f"\r🤖 Consultando IA sobre: {musica[:20]}...", end="")
                    info_ia = consultar_gemini_info(musica, artista)
                    
                    # Prepara dados extras
                    dados_extras = {
                        "explicit": " (E)" in el.text,
                        "album": info_ia.get("album", "Single"),
                        "genero": info_ia.get("genero", "Música")
                    }
                    
                    # Salva no ChromaDB
                    memoria.memorizar_musica(
                        musica=musica, 
                        artista=artista, 
                        tags=contexto_tag,
                        extra_info=dados_extras
                    )
                    
                    print(f"\r📥 [{total_processado}] {musica[:25]:<25} | {artista[:15]:<15} | 🎹 {dados_extras['genero']}")
                    
                    # Pausa pequena para não estourar a API do Gemini
                    time.sleep(0.5) 
            except Exception as e:
                continue

        scroll_focado_no_centro(driver)
        time.sleep(1.2) 
        
        if novos_nesta_tela == 0:
            tentativas_sem_novidade += 1
            print(".", end="", flush=True) 
            if tentativas_sem_novidade >= 10: # Reduzi para 10 pra ser mais ágil
                print("\n🏁 Processo concluído.")
                break
        else:
            tentativas_sem_novidade = 0
            
    return total_processado

def menu():
    try:
        driver = conectar_edge_debug()
        print("\n" + "="*60)
        print("🎯 SPOTIFY SCRAPER V3 - COM ENRIQUECIMENTO GEMINI")
        print("="*60)
        print("1. Extrair Músicas Curtidas")
        print("2. Extrair Playlist Atual (Acadus, Louvor, etc)")
        
        opt = input("\nOpção: ")
        
        if opt == "1":
            driver.get("https://open.spotify.com/collection/tracks") # Hack para forçar foco
            time.sleep(2)
            extrair_playlist(driver, "spotify_likes")
        
        elif opt == "2":
            nome = input("Nome da Playlist (ex: louvor): ")
            print(f"👉 Abra a playlist '{nome}' e deixe o mouse no centro.")
            input("Pressione Enter para começar...")
            extrair_playlist(driver, f"playlist_{nome}")
            
    except Exception as e:
        log.critical(f"Erro: {e}")

if __name__ == "__main__":
    menu()