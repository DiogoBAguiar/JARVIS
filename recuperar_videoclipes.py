import os
import sys
import json
import time
import re
import warnings

# Limpa logs do sistema
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

# --- CONFIGURAÇÃO ---
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("❌ ERRO: Chave API ausente no .env")
    sys.exit(1)

client = genai.Client(api_key=API_KEY)

def limpar_nome_para_pesquisa(texto):
    texto = re.sub(r"[\(\[].*?[\)\]]", "", texto)
    termos_lixo = ["videoclipe", "official", "video", "clip", "ao vivo", "live", "remaster", "4k", "hd", "lyrics", "letra"]
    for t in termos_lixo:
        texto = re.sub(f"(?i){re.escape(t)}", "", texto)
    texto = re.sub(r"\b\d{4}\b", "", texto)
    texto = re.sub(r"[-/|]", "", texto)
    return texto.strip()

def pesquisar_na_web(termo_original):
    try:
        termo_limpo = limpar_nome_para_pesquisa(termo_original)
        busca = termo_limpo if len(termo_limpo) > 2 else termo_original
        query = f'musica song "{busca}" artist'
        
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=1))
            if results:
                return f"{results[0]['title']}: {results[0]['body']}"
    except: pass
    return None

def limpar_json(texto):
    # Remove blocos de código markdown que o Gemma adora colocar
    texto = texto.replace("```json", "").replace("```", "").strip()
    # Tenta achar onde começa o JSON ({) e onde termina (})
    try:
        inicio = texto.find("{")
        fim = texto.rfind("}") + 1
        if inicio != -1 and fim != -1:
            return texto[inicio:fim]
    except: pass
    return texto

def consultar_gemma(prompt):
    """
    Usa GEMMA 3 sem forçar mode JSON nativo (que causa erro 400).
    Confia no prompt para gerar JSON.
    """
    modelos = ["gemma-3-27b-it", "gemma-3-12b-it"]
    
    for modelo in modelos:
        try:
            response = client.models.generate_content(
                model=modelo,
                contents=prompt,
                config=types.GenerateContentConfig(
                    # response_mime_type="application/json", <--- REMOVIDO! O Gemma odeia isso.
                    temperature=0.1
                )
            )
            return limpar_json(response.text)

        except Exception as e:
            if "429" in str(e): # Se der rate limit, tenta o modelo menor
                continue
            # Ignora erros e tenta o próximo
            continue
    
    return "{}"

def recuperar_artistas():
    print("💎 INICIANDO RESGATE (GEMMA 3 - MODO TEXTO)...")
    print("🚀 Usando cota de alta capacidade.")
    
    if not memoria._conectar(): return
    
    dados = memoria.collection.get()
    ids = dados['ids']
    metadatas = dados['metadatas']
    
    alvos = []
    
    for i, meta in enumerate(metadatas):
        musica = meta.get('musica', '').lower()
        artista = meta.get('artista', '').lower()
        
        if musica in ["desconhecida", "desconhecido", "track", "faixa", ""] or len(musica) < 2:
            continue
        if "videoclip" in artista or "video clip" in artista or "desconhecido" in artista: 
            alvos.append((i, ids[i], meta))
            
    total = len(alvos)
    print(f"🚩 Encontrados {total} registros para corrigir.")
    
    sucessos = 0
    
    for idx, (original_index, doc_id, meta) in enumerate(alvos):
        titulo_sujo = meta.get('musica', '')
        
        print(f"\n🔍 [{idx+1}/{total}] Investigando: '{titulo_sujo}'")
        
        contexto = pesquisar_na_web(titulo_sujo)
        
        prompt = f"""
        Identify REAL Artist and Song Name.
        Input: "{titulo_sujo}"
        Web Context: {contexto if contexto else 'Use internal knowledge'}
        
        STRICT OUTPUT FORMAT: Return ONLY a raw JSON string. No markdown, no explanations.
        Example: {{ "artista_real": "Coldplay", "musica_real": "Yellow" }}
        
        Target JSON:
        """
        
        res_json_str = consultar_gemma(prompt)
        
        try:
            dados_novos = json.loads(res_json_str)
            novo_artista = dados_novos.get('artista_real', 'Desconhecido')
            nova_musica = dados_novos.get('musica_real', 'Desconhecida')
            
            if novo_artista in ["Desconhecido", "Videoclipe", "Artist"]:
                print(f"   ⚠️ Falha na identificação.")
                continue

            print(f"   ✅ GEMMA: {novo_artista} - {nova_musica}")
            
            novo_meta = meta.copy()
            novo_meta['artista'] = novo_artista
            novo_meta['musica'] = nova_musica
            
            if novo_artista in ["Matuê", "WIU", "Teto"]: novo_meta['genero'] = "Trap"
            elif novo_artista in ["Bon Jovi", "Coldplay", "Oasis"]: novo_meta['genero'] = "Rock/Pop"
            else: novo_meta['genero'] = "Música"
            
            doc_novo = f"Música: {nova_musica}. Artista: {novo_artista}. Gênero: {novo_meta['genero']}."
            
            memoria.collection.upsert(ids=[doc_id], metadatas=[novo_meta], documents=[doc_novo])
            sucessos += 1

        except:
            print(f"   ❌ Erro ao ler JSON (Gemma respondeu texto?). Resposta: {res_json_str[:50]}...")
        
        # Pausa de 3s para o Gemma
        time.sleep(3)

    print(f"\n🏁 Fim. {sucessos} corrigidos.")

if __name__ == "__main__":
    recuperar_artistas()