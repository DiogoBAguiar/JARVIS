import os
import sys
import json
import time
import re
import ollama 
from dotenv import load_dotenv
from duckduckgo_search import DDGS
from groq import Groq 

# Carrega ambiente
load_dotenv()
sys.path.append(os.getcwd())

from jarvis_system.hipocampo.memoria import memoria

# --- CONFIGURAÇÕES DE ENERGIA ---
MODELO_NUVEM = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
MODELO_LOCAL = os.getenv("JARVIS_MODEL_LOCAL", "llama3.2:1b")
API_KEY = os.getenv("GROQ_API_KEY")

print(f"⚙️ CONFIGURAÇÃO ATIVA:")
print(f"   ☁️  Nuvem (Prioridade): {MODELO_NUVEM}")
print(f"   🏠 Local (Backup):     {MODELO_LOCAL}")

# Cliente Groq
client_groq = Groq(api_key=API_KEY) if API_KEY else None

# --- CONHECIMENTO PRÉVIO (HARDCODED) ---
# Isso ajuda a IA a não alucinar gêneros em artistas conhecidos
ARTIST_GENRE_MAP = {
    # Trap / Rap / Hip Hop
    "matuê": "Trap", "wiu": "Trap", "teto": "Trap", "30praum": "Trap",
    "felipe ret": "Trap/Rap", "oro": "Trap", "orochi": "Trap", "poze": "Funk/Trap",
    "l7nnon": "Rap/Funk", "djonga": "Rap", "bk": "Rap", "tz da coronel": "Trap",
    "kayblack": "Trap", "veigh": "Trap", "major rd": "Drill/Rap", "lil whind": "Trap/Comedy",
    "1nonly": "Aesthetic Rap", "post malone": "Hip Hop/Pop", "travis scott": "Hip Hop",
    
    # Piseiro / Forró / Sertanejo
    "joão gomes": "Piseiro", "tarcísio do acordeon": "Piseiro", "vitor fernandes": "Piseiro",
    "felipe amorim": "Piseiro/Pop", "nattan": "Forró/Pop", "mari fernandez": "Piseiro",
    "zé felipe": "Sertanejo/Pop", "ana castela": "Agro-nejo",
    
    # Funk
    "mc daniel": "Funk", "mc ryan sp": "Funk", "mc hariel": "Funk", "mc kevin": "Funk",
    "anitta": "Pop/Funk", "ludmilla": "Pop/Funk/Pagode",
    
    # Pop / Gospel / Outros
    "priscilla": "Pop", "priscilla alcantara": "Pop/Gospel", 
    "luísa sonza": "Pop", "pabllo vittar": "Pop/Drag", "gloria groove": "Pop/Rap",
    "jão": "Pop", "marina sena": "Pop", "lagum": "Pop/Alternative"
}

def limpar_termo_pesquisa(texto):
    if not texto: return ""
    texto = re.sub(r'\s*\(.*?\)', '', texto)
    texto = re.sub(r'\s*\[.*?\]', '', texto)
    termos = ["Feat.", "feat.", "Ft.", "ft.", "Remaster", "Ao Vivo", "Live", "Official Video", "Video", "Lyrics", "Letra"]
    for t in termos: texto = texto.replace(t, "")
    return texto.strip()

def pesquisar_na_web(termo):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(termo, max_results=1))
            if results: return f"{results[0]['title']}: {results[0]['body']}"
    except: pass
    return None

def extrair_json_da_resposta(texto_ia):
    try:
        return json.loads(texto_ia)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', texto_ia, re.DOTALL)
        if match:
            try: return json.loads(match.group())
            except: pass
    return None

def consultar_ia_nuvem(prompt):
    if not client_groq: raise Exception("Sem API Key")
    completion = client_groq.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=MODELO_NUVEM,
        temperature=0.1, # Temperatura baixíssima para respeitar regras estritas
        response_format={"type": "json_object"}
    )
    return completion.choices[0].message.content

def consultar_ia_local(prompt):
    try:
        response = ollama.chat(model=MODELO_LOCAL, messages=[
            {'role': 'user', 'content': prompt}
        ], options={'temperature': 0.1})
        return response['message']['content']
    except Exception as e:
        print(f"   ☠️ Erro fatal na IA Local: {e}")
        return "{}"

def identificar_genero_forcado(artista):
    """Verifica se o artista tem um gênero pré-definido no mapa."""
    artista_lower = artista.lower()
    for key, genero in ARTIST_GENRE_MAP.items():
        if key in artista_lower:
            return genero
    return None

def enriquecer_com_ia():
    print(f"\n🚀 INICIANDO PROCESSAMENTO EM LOTE (HÍBRIDO + REGRAS)")
    
    if not memoria._conectar(): return
    
    dados = memoria.collection.get()
    ids = dados['ids']
    metadatas = dados['metadatas']
    total = len(ids)
    
    pulos = 0
    sucessos = 0

    for i, meta in enumerate(metadatas):
        # 1. VERIFICAÇÃO RÁPIDA
        if meta.get("genero") and meta.get("album") and meta.get("genero") != "Desconhecido":
            pulos += 1
            if pulos % 100 == 0: print(f"⏩ Pulando processados... ({pulos}/{total})")
            continue

        musica = meta.get('musica', 'Desconhecida')
        artista = meta.get('artista', 'Desconhecido')
        
        # Limpeza
        musica_busca = limpar_termo_pesquisa(musica)
        artista_busca = limpar_termo_pesquisa(artista).split(",")[0]

        print(f"\n🔎 [{i + 1}/{total}] {musica_busca} - {artista_busca}")

        # 2. BUSCA WEB
        contexto_web = pesquisar_na_web(f"{musica_busca} {artista_busca} genre album release year")
        
        # 3. VERIFICAÇÃO DE REGRA DE ARTISTA (Inject Knowledge)
        dica_genero = identificar_genero_forcado(artista)
        texto_dica = ""
        if dica_genero:
            texto_dica = f"IMPORTANT RULE: The artist '{artista}' is famously known for the genre '{dica_genero}'. PREFER this genre unless the specific song is drastically different."

        # 4. PROMPT OTIMIZADO E ESPECÍFICO
        prompt = f"""
        Analyze the song "{musica}" by "{artista}".
        Context from web: {contexto_web if contexto_web else 'Not available'}
        
        {texto_dica}

        Task: Identify the Album Name, main Genre, and Release Year.
        
        CRITICAL GENRE GUIDELINES:
        1. Distinguish carefully between: Sertanejo, Funk (Brazilian), Trap, Rap, Piseiro, and Pop.
        2. Do NOT label Trap/Rap artists (like Matuê, WIU, Teto) as Sertanejo.
        3. Do NOT label Piseiro artists (like João Gomes) as Sertanejo unless specified.
        4. "1nonly" is Aesthetic Rap/Trap.
        
        Return JSON ONLY:
        {{
            "album": "Album Name (or Single)",
            "genero": "Genre (e.g. Trap, Funk, Sertanejo, Piseiro, Pop, Rock)",
            "ano": "YYYY"
        }}
        """

        resposta_texto = ""
        origem = ""
        usou_web = "WEB" if contexto_web else "NO_WEB"

        try:
            # Tenta Nuvem
            resposta_texto = consultar_ia_nuvem(prompt)
            origem = "☁️ NUVEM (8b)"
        except Exception as e:
            erro_msg = str(e).lower()
            if "429" in erro_msg:
                print(f"   ⚠️ Rate Limit no Groq. Mudando para LOCAL...")
            else:
                print(f"   ⚠️ Erro Groq ({e}). Mudando para LOCAL...")
            
            # Tenta Local
            resposta_texto = consultar_ia_local(prompt)
            origem = f"🏠 LOCAL ({MODELO_LOCAL})"

        # Processamento
        dados_novos = extrair_json_da_resposta(resposta_texto)
        if not dados_novos: dados_novos = {}

        genero = dados_novos.get("genero", "Desconhecido")
        album = dados_novos.get("album", "Desconhecido")
        ano = str(dados_novos.get("ano", "?"))

        # Upsert
        novo_meta = meta.copy()
        novo_meta.update({
            "album": album,
            "genero": genero,
            "ano_lancamento": ano,
            "origem_dados": f"{origem} + {usou_web}"
        })
        
        doc_novo = f"Música: {musica}. Artista: {artista}. Álbum: {album}. Gênero: {genero}. Ano: {ano}"
        
        try:
            memoria.collection.upsert(ids=[ids[i]], documents=[doc_novo], metadatas=[novo_meta])
            
            status = "✅"
            if genero == "Desconhecido": status = "⚠️"
            
            # Mostra no log se usou a Regra de Artista
            if dica_genero and dica_genero.lower() in genero.lower():
                status = "🎯" # Acertou na mosca com a dica
            
            print(f"   {status} {origem}: {album} | {genero} | {ano}")
            sucessos += 1
        except Exception as e:
            print(f"   ❌ Erro BD: {e}")

        time.sleep(0.5)

    print(f"\n🏁 FIM DO LOTE. Sucessos: {sucessos}")

if __name__ == "__main__":
    enriquecer_com_ia()