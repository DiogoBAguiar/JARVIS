import os
import sys
import uuid
import warnings

# Limpa logs
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"
warnings.filterwarnings("ignore")

from dotenv import load_dotenv
load_dotenv()
sys.path.append(os.getcwd())

from jarvis_system.hipocampo.memoria import memoria

# --- DADOS CORRETOS (GABARITO) ---
# Vamos forçar esses dados no banco, independente do que a IA ache.
RESGATE_LOL = [
    {
        "musica": "Take Over",
        "artista": "League of Legends",
        "genero": "Soundtrack/Game",
        "feat": "Jeremy McKinnon, MAX, Henry"
    },
    {
        "musica": "RISE",
        "artista": "League of Legends",
        "genero": "Soundtrack/Game",
        "feat": "The Glitch Mob, Mako, The Word Alive"
    },
    {
        "musica": "Phoenix",
        "artista": "League of Legends",
        "genero": "Soundtrack/Game",
        "feat": "Cailin Russo, Chrissy Costanza"
    },
    {
        "musica": "Awaken",
        "artista": "League of Legends",
        "genero": "Soundtrack/Game",
        "feat": "Valerie Broussard"
    },
    {
        "musica": "Legends Never Die",
        "artista": "League of Legends",
        "genero": "Soundtrack/Game",
        "feat": "Against The Current"
    },
    {
        "musica": "Warriors",
        "artista": "Imagine Dragons", # Essa é creditada à banda mesmo
        "genero": "Soundtrack/Game",
        "feat": "League of Legends World Championship 2014"
    }
]

def cirurgia_banco():
    print("🏥 INICIANDO CIRURGIA DE DADOS...")
    
    if not memoria._conectar(): 
        print("❌ Erro ao conectar no Hipocampo.")
        return

    collection = memoria.collection
    
    # --- PASSO 1: REMOVER ALUCINAÇÕES ---
    print("\n🧹 Passo 1: Removendo alucinações ('Walter Racklee')...")
    # Busca por artista errado gerado no loop anterior
    result = collection.get(where={"artista": "Walter Racklee"})
    ids_lixo = result['ids']
    
    if ids_lixo:
        collection.delete(ids=ids_lixo)
        print(f"   🗑️ {len(ids_lixo)} registros de 'Walter Racklee' deletados.")
    else:
        print("   ✅ Nenhum lixo encontrado.")

    # --- PASSO 2: CORRIGIR/RESSUSCITAR LOL ---
    print("\n💉 Passo 2: Restaurando trilha sonora do League of Legends...")
    
    for item in RESGATE_LOL:
        # Tenta achar a música pelo nome (mesmo que o artista esteja errado)
        # Nota: ChromaDB é chato com busca exata, vamos tentar listar e filtrar
        # Como não dá pra fazer query complexa fácil, vamos inserir/sobrescrever
        
        # Procura se já existe algo parecido
        busca = collection.get(where={"musica": item["musica"]})
        
        doc_texto = f"Música: {item['musica']}. Artista: {item['artista']} ({item['feat']}). Gênero: {item['genero']}."
        meta_novo = {
            "musica": item["musica"],
            "artista": item["artista"],
            "genero": item["genero"]
        }

        if len(busca['ids']) > 0:
            # Se achou (ex: Phoenix que estava errado), atualiza
            id_existente = busca['ids'][0]
            print(f"   🔧 Corrigindo: {item['musica']} (ID: {id_existente})")
            collection.update(
                ids=[id_existente],
                metadatas=[meta_novo],
                documents=[doc_texto]
            )
        else:
            # Se não achou (foi deletado), recria
            novo_id = f"restored_lol_{uuid.uuid4().hex[:8]}"
            print(f"   ✨ Ressuscitando: {item['musica']} (Novo ID)")
            collection.add(
                ids=[novo_id],
                metadatas=[meta_novo],
                documents=[doc_texto]
            )

    print("\n🏁 CIRURGIA CONCLUÍDA COM SUCESSO.")
    print("   O banco de dados agora está higienizado.")

if __name__ == "__main__":
    cirurgia_banco()