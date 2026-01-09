import os
import sys
import json
import time
import re
import warnings

os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"
warnings.filterwarnings("ignore")

from dotenv import load_dotenv
from duckduckgo_search import DDGS
from google import genai
from google.genai import types

load_dotenv()
sys.path.append(os.getcwd())

from jarvis_system.hipocampo.memoria import memoria

API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

# Lista de artistas que são CERTAMENTE lixo
ARTISTAS_LIXO = ["Desconhecido", "Videoclipe", "É", "•", "Unknown", "Artistas Diversos", "Artist"]

def limpar_json(texto):
    texto = texto.replace("```json", "").replace("```", "").strip()
    try:
        inicio = texto.find("{")
        fim = texto.rfind("}") + 1
        if inicio != -1 and fim != -1:
            return texto[inicio:fim]
    except: pass
    return texto

def pesquisar_web(termo):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f'quem canta "{termo}" musica', max_results=1))
            if results: return f"{results[0]['title']} {results[0]['body']}"
    except: pass
    return None

def consultar_gemma(prompt):
    try:
        response = client.models.generate_content(
            model="gemma-3-27b-it",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.1)
        )
        return limpar_json(response.text)
    except: return "{}"

def faxina_final():
    print("🧹 INICIANDO A FAXINA FINAL (COM PROTEÇÃO PARA GAMERS)...")
    
    if not memoria._conectar(): return
    dados = memoria.collection.get()
    ids = dados['ids']
    metadatas = dados['metadatas']
    
    alvos = []
    
    # 1. Identificar Registros Problemáticos
    for i, meta in enumerate(metadatas):
        artista = meta.get('artista', 'Desconhecido')
        
        # Critérios para entrar na faxina:
        # 1. Está na lista de lixo
        # 2. Tem menos de 2 letras
        # 3. É do LoL mas está formatado errado (com vírgulas perdidas)
        if (artista in ARTISTAS_LIXO) or (len(artista) < 2) or ("League of Legends" in artista and "," in artista):
            alvos.append((ids[i], meta))

    print(f"🚩 Encontrados {len(alvos)} itens para corrigir.")

    deletados = 0
    corrigidos = 0

    for doc_id, meta in alvos:
        musica_suja = meta.get('musica', '')
        artista_atual = meta.get('artista', '')

        print(f"\n🔍 Analisando: '{musica_suja}' (Artista Atual: {artista_atual})")
        
        # 2. Proteção contra arquivos de sistema/audio
        if re.search(r'(whatsapp|audio|rec_|faixa|track|unknown|\d{8})', musica_suja.lower()) and len(musica_suja) < 15:
            print("   🗑️ Arquivo de áudio genérico -> Deletando...")
            memoria.collection.delete(ids=[doc_id])
            deletados += 1
            continue

        # 3. Busca Contexto
        contexto = pesquisar_web(musica_suja)
        
        # 4. Prompt Específico para Salvar Soundtracks
        prompt = f"""
        Identify REAL Artist and Song.
        Input Title: "{musica_suja}"
        Current Artist Info: "{artista_atual}"
        Web Context: {contexto}
        
        Rules:
        1. If it's a Game Soundtrack (e.g., League of Legends), set artist as "League of Legends" or the specific singer.
        2. If it's "Take Over", Artist is "League of Legends" (or Jeremy McKinnon).
        3. If it looks like garbage/noise, return "DELETE".
        
        STRICT JSON OUTPUT:
        {{ "artista": "Name", "musica": "Title" }}
        """
        
        res = consultar_gemma(prompt)
        
        try:
            dados_novos = json.loads(res)
            novo_artista = dados_novos.get('artista', 'Desconhecido')
            nova_musica = dados_novos.get('musica', 'Desconhecida')

            # Se a IA mandar deletar OU devolver "Desconhecido" de novo, aí sim deletamos
            if novo_artista == "DELETE" or (novo_artista in ARTISTAS_LIXO and "League" not in artista_atual):
                print("   🗑️ Irrecuperável -> Deletando.")
                memoria.collection.delete(ids=[doc_id])
                deletados += 1
            else:
                print(f"   ✨ RECUPERADO: {novo_artista} - {nova_musica}")
                
                # Define Gênero se for LoL
                genero = meta.get('genero', 'Música')
                if "League of Legends" in novo_artista or "Riot" in novo_artista:
                    genero = "Soundtrack/Game"
                
                novo_meta = meta.copy()
                novo_meta['artista'] = novo_artista
                novo_meta['musica'] = nova_musica
                novo_meta['genero'] = genero
                
                doc_novo = f"Música: {nova_musica}. Artista: {novo_artista}. Gênero: {genero}."
                
                memoria.collection.upsert(ids=[doc_id], metadatas=[novo_meta], documents=[doc_novo])
                corrigidos += 1
        except:
            print("   ⚠️ Erro na IA. Pulando.")
        
        time.sleep(2)

    print(f"\n🏁 FIM DA FAXINA.")
    print(f"   ✨ Recuperados: {corrigidos}")
    print(f"   🗑️ Lixo Removido: {deletados}")

if __name__ == "__main__":
    faxina_final()