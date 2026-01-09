import os
import sys
import time
import re
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By

# Adiciona raiz ao path
sys.path.append(os.getcwd())

from jarvis_system.hipocampo.memoria import memoria
from jarvis_system.cortex_frontal.observability import JarvisLogger

log = JarvisLogger("SPOTIFY_V3_FINAL")

def conectar_edge_debug():
    """Conecta ao Edge que já está aberto na porta 9222."""
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    base_dir = os.getcwd()
    driver_local = os.path.join(base_dir, "msedgedriver.exe")
    service = Service(driver_local) if os.path.exists(driver_local) else Service()
    
    return webdriver.Edge(service=service, options=options)

def limpar_texto(texto_bruto):
    """
    Remove ruídos visuais e o 'E' (Explicit) do texto extraído.
    """
    if not texto_bruto: return None, None
    linhas = [l.strip() for l in texto_bruto.split('\n') if l.strip()]
    
    lixo_exato = ["E", "Explicit", "Lyrics", "Letra", "Tocando", "Playing", "Ao vivo", "Live", "Video"]
    
    limpo = []
    for l in linhas:
        if re.match(r'^\d+$', l): continue
        if re.match(r'^\d+:\d+$', l): continue
        if l in lixo_exato: continue
        
        # Remove prefixo "E " do início do nome
        l_limpa = re.sub(r'^E\s+', '', l)
        limpo.append(l_limpa)
    
    if len(limpo) < 2: return None, None
    return limpo[0], limpo[1]

def scroll_focado_no_centro(driver):
    """
    Rola o container que está sob o centro da tela.
    """
    try:
        driver.execute_script("""
            var x = window.innerWidth / 2;
            var y = window.innerHeight / 2;
            var elemento = document.elementFromPoint(x, y);
            
            while (elemento) {
                const style = window.getComputedStyle(elemento);
                if (style.overflowY === 'scroll' || style.overflowY === 'auto' || style.overflowY === 'overlay') {
                    elemento.scrollBy(0, 700);
                    return;
                }
                elemento = elemento.parentElement;
            }
            window.scrollBy(0, 700);
        """)
    except Exception as e:
        log.warning(f"Erro no scroll: {e}")

def extrair_playlist(driver, contexto_tag="spotify_likes"):
    log.info(f"📜 Iniciando extração ESTRUTURADA: {contexto_tag}")
    
    coletados = set()
    tentativas_sem_novidade = 0
    total_processado = 0
    
    time.sleep(1)

    while True:
        # 1. CAPTURA
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
                    
                    # MODIFICAÇÃO: Chamada ao novo método profissional do Hipocampo
                    # O 'upsert' interno evita duplicatas com as 887 músicas já migradas.
                    memoria.memorizar_musica(
                        musica=musica, 
                        artista=artista, 
                        tags=contexto_tag,
                        extra_info={"explicit": " (E)" in el.text}
                    )
                    
                    print(f"\r📥 [{total_processado}] {musica[:25]:<25} | {artista[:20]}", end="")
            except Exception as e:
                continue

        # 2. ROLA
        scroll_focado_no_centro(driver)
        time.sleep(1.2) 
        
        # 3. CRITÉRIO DE PARADA
        if novos_nesta_tela == 0:
            tentativas_sem_novidade += 1
            print(".", end="", flush=True) 
            if tentativas_sem_novidade >= 15:
                print("\n🏁 Processo concluído.")
                break
        else:
            tentativas_sem_novidade = 0
            
    return total_processado

def menu():
    try:
        driver = conectar_edge_debug()
        print("\n" + "="*60)
        print("🎯 SPOTIFY SCRAPER V3.5 - HYBRID METADATA")
        print("="*60)
        print("1. Extrair Músicas Curtidas")
        print("2. Extrair Playlist Atual (Acadus, etc)")
        
        opt = input("\nOpção: ")
        
        if opt == "1":
            driver.get("https://open.spotify.com/collection/tracks")
            time.sleep(3)
            extrair_playlist(driver, "spotify_likes")
        
        elif opt == "2":
            nome = input("Nome da Playlist (ex: acadus): ")
            print(f"👉 Abra a playlist '{nome}' e deixe o mouse no centro.")
            input("Pressione Enter para começar...")
            extrair_playlist(driver, f"playlist_{nome}")
            
    except Exception as e:
        log.critical(f"Erro: {e}")

if __name__ == "__main__":
    menu()