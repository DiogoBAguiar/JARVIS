import os
import sys
import requests
import time
import warnings

# Limpa logs desnecessários
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"
warnings.filterwarnings("ignore")

# Garante raiz do projeto
sys.path.append(os.getcwd())
from jarvis_system.hipocampo.memoria import memoria

def buscar_metadados_reais(artista, musica):
    """
    Busca Ano e Álbum na base de dados da Apple/iTunes.
    """
    try:
        termo = f"{artista} {musica}".replace(" ", "+")
        # Busca limitada a 1 resultado para ser rápido
        url = f"https://itunes.apple.com/search?term={termo}&media=music&limit=1"
        
        resp = requests.get(url, timeout=3)
        if resp.status_code == 200:
            dados = resp.json()
            if dados['resultCount'] > 0:
                item = dados['results'][0]
                data_completa = item.get('releaseDate', '')
                
                return {
                    'ano': data_completa[:4] if data_completa else 'Desconhecido',
                    'album_real': item.get('collectionName', 'Single'),
                    'capa': item.get('artworkUrl100', '').replace('100x100', '600x600')
                }
    except:
        pass
    return None

def preencher_anos():
    print("⏳ INICIANDO VIAGEM NO TEMPO (RECUPERANDO ANOS DE LANÇAMENTO)...")
    
    if not memoria._conectar(): return
    collection = memoria.collection
    
    # Pega todas as músicas
    dados = collection.get()
    ids = dados['ids']
    metadatas = dados['metadatas']
    total = len(ids)
    
    atualizados = 0
    
    print(f"   🔎 Analisando {total} faixas na memória...")

    for i, meta in enumerate(metadatas):
        doc_id = ids[i]
        artista = meta.get('artista', '')
        musica = meta.get('musica', '')
        ano_atual = meta.get('ano')
        
        # Critério: Se não tem ano, ou o ano é "-", ou é muito curto
        precisa_atualizar = (not ano_atual) or (str(ano_atual) in ["-", "None", ""])
        
        if precisa_atualizar:
            print(f"   📅 [{i+1}/{total}] Buscando ano para: {musica} ({artista})...", end="")
            
            info = buscar_metadados_reais(artista, musica)
            
            if info and info['ano'] != 'Desconhecido':
                print(f" ✅ Achou: {info['ano']}")
                
                # Atualiza metadados
                novo_meta = meta.copy()
                novo_meta['ano'] = info['ano']
                
                # Se não tiver álbum ou capa, aproveita e preenche
                if not meta.get('album') or meta.get('album') == '-':
                    novo_meta['album'] = info['album_real']
                if not meta.get('capa_url'):
                    novo_meta['capa_url'] = info['capa']
                
                # Atualiza documento de texto para a IA saber o ano
                doc_original = dados['documents'][i]
                novo_doc = f"{doc_original} Ano: {info['ano']}."
                
                collection.update(
                    ids=[doc_id],
                    metadatas=[novo_meta],
                    documents=[novo_doc]
                )
                atualizados += 1
            else:
                print(f" ❌ Não encontrado.")
            
            # Respeitar limite da API
            time.sleep(0.3)
            
    print("\n" + "="*50)
    print(f"🏁 FIM DA VIAGEM NO TEMPO.")
    print(f"   ✨ Total de datas recuperadas: {atualizados}")

if __name__ == "__main__":
    preencher_anos()