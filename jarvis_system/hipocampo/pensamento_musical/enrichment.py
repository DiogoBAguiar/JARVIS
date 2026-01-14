import time
import requests

class MusicEnrichment:
    def __init__(self, collection, logger_func):
        self.collection = collection
        self.log = logger_func

    def buscar_anos_faltantes(self):
        if not self.collection: return
        self.log("⏳ Buscando anos e capas na Apple Music/iTunes...")
        
        dados = self.collection.get()
        ids = dados['ids']
        metadatas = dados['metadatas']
        count = 0
        
        for i, meta in enumerate(metadatas):
            if not meta.get('ano') or str(meta.get('ano')) in ['-', 'None', '']:
                artista = meta.get('artista', '')
                musica = meta.get('musica', '')
                
                try:
                    termo = f"{artista} {musica}".replace(" ", "+")
                    url = f"https://itunes.apple.com/search?term={termo}&media=music&limit=1"
                    res = requests.get(url, timeout=2)
                    
                    if res.status_code == 200 and res.json()['resultCount'] > 0:
                        item = res.json()['results'][0]
                        ano = item['releaseDate'][:4]
                        
                        novo_meta = meta.copy()
                        novo_meta['ano'] = ano
                        if not novo_meta.get('album') or novo_meta.get('album') == 'Single':
                            novo_meta['album'] = item['collectionName']
                        if not novo_meta.get('capa_url'):
                            novo_meta['capa_url'] = item['artworkUrl100'].replace('100x100', '600x600')
                        
                        doc_antigo = dados['documents'][i]
                        doc_novo = f"{doc_antigo} Ano: {ano}."
                        
                        self.collection.update(ids=[ids[i]], metadatas=[novo_meta], documents=[doc_novo])
                        print(f"   ✅ {musica}: {ano}")
                        count += 1
                        time.sleep(0.3)
                except: pass
        self.log(f"Processo finalizado. {count} músicas enriquecidas.")