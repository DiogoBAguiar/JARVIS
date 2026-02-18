import logging
import re
from collections import Counter

class MusicMaintenance:
    def __init__(self, collection, logger_func):
        self.collection = collection
        self.log = logger_func

    def remover_lixo(self):
        if not self.collection: return
        self.log("🧹 Removendo registros inválidos...")
        lixo = self.collection.get(where={"artista": "Videoclipe"})
        if lixo['ids']:
            self.collection.delete(ids=lixo['ids'])
            self.log(f"🗑️ Removidos {len(lixo['ids'])} itens 'Videoclipe'.")
        else:
            self.log("Nenhum lixo crítico encontrado.")

    def refinar_generos(self):
        if not self.collection: return
        self.log("💎 Refinando Gêneros Musicais...")
        
        MAPA = {
            "Forró/Piseiro": ["Wesley Safadão", "João Gomes", "NATTAN", "Barões", "Felipe Amorim", "Tarcísio", "Raí Saia Rodada", "Mari Fernandez", "Avine Vinny"],
            "Rock": ["Linkin Park", "Nirvana", "Red Hot", "System of a Down", "Evanescence", "Skank", "Charlie Brown", "Audioslave", "Foo Fighters", "Pearl Jam", "Nickelback", "AC/DC", "Guns N"],
            "Hip-Hop/Rap": ["Eminem", "Drake", "Post Malone", "1Kilo", "Hungria", "Tupac", "50 Cent", "Snoop Dogg", "Jay-Z", "Kanye West", "Wiz Khalifa", "Black Eyed Peas", "Kendrick Lamar", "Travis Scott", "Coolio"],
            "Trap": ["Matuê", "Teto", "WIU", "Brandão85", "Sidoka", "Veigh", "KayBlack", "MC Cabelinho", "Orochi"],
            "Pop": ["Justin Bieber", "Coldplay", "Maroon 5", "Imagine Dragons", "Ed Sheeran", "Bruno Mars", "Dua Lipa", "Rihanna", "Lady Gaga"],
            "Católica/Worship": ["Frei Gilson", "Padre", "Worship", "Colo de Deus", "Fernandinho", "Casa Worship", "Gabriela Rocha", "Morada", "Rosa de Saron", "Thiago Brado", "Som do Monte"],
            "Reggae/Vibe": ["Natiruts", "Maneva", "Melim", "Lagum", "Vitor Kley", "Armandinho"],
            "Eletrônica": ["Alok", "Vintage Culture", "Avicii", "David Guetta", "Calvin Harris", "Martin Garrix", "Tiësto", "Marshmello"]
        }

        dados = self.collection.get()
        ids = dados['ids']
        metadatas = dados['metadatas']
        documents = dados['documents']
        count = 0

        for i, meta in enumerate(metadatas):
            artista = meta.get('artista', '')
            genero_atual = meta.get('genero', '')
            
            for gen_alvo, lista in MAPA.items():
                if any(x.lower() in artista.lower() for x in lista):
                    if genero_atual != gen_alvo:
                        nm = meta.copy()
                        nm['genero'] = gen_alvo
                        
                        doc = documents[i].replace(f"Gênero: {genero_atual}", f"Gênero: {gen_alvo}")
                        if gen_alvo not in doc: doc += f" Gênero: {gen_alvo}."
                        
                        self.collection.update(ids=[ids[i]], metadatas=[nm], documents=[doc])
                        print(f"   🎸 {artista}: {genero_atual} -> {gen_alvo}")
                        count += 1
                    break
        self.log(f"{count} gêneros reclassificados.")

    def corrigir_nomes_artistas(self):
        """
        Usa estatística para corrigir nomes cortados (Ex: ', So' -> ', Som do Monte')
        baseado nos artistas que já existem corretamente no banco.
        """
        if not self.collection: return
        self.log("🧠 Iniciando Autocorreção Inferencial de Artistas...")

        dados = self.collection.get()
        ids = dados['ids']
        metadatas = dados['metadatas']
        documents = dados['documents']

        # 1. FASE DE APRENDIZADO (Estatística)
        # Coleta todos os artistas INDIVIDUAIS corretos do banco
        contador_artistas = Counter()
        
        for meta in metadatas:
            artista_full = meta.get('artista', '')
            # Separa por vírgula ou ' feat '
            partes = re.split(r', | feat\. | & ', artista_full)
            for p in partes:
                p = p.strip()
                # Consideramos "Válido" se tiver mais de 3 letras e não terminar em pontuação
                if len(p) > 3 and not p.endswith(('.', ',')):
                    contador_artistas[p] += 1

        self.log(f"📚 Base de conhecimento: {len(contador_artistas)} artistas únicos identificados.")

        # 2. FASE DE CORREÇÃO
        count = 0
        
        # Mapa manual para casos muito específicos que a estatística pode errar
        MAPA_MANUAL = {
            "Frei Gilson, So": "Frei Gilson, Som do Monte",
            "Frei Gilson, Br": "Frei Gilson, Bruna Ramos"
        }

        for i, meta in enumerate(metadatas):
            artista_atual = meta.get('artista', '')
            novo_artista = artista_atual
            changed = False

            # A. Tenta correção manual primeiro
            for errado, correto in MAPA_MANUAL.items():
                if artista_atual.endswith(errado):
                    novo_artista = correto
                    changed = True
                    break

            # B. Se não corrigiu, tenta correção ESTATÍSTICA
            if not changed and ", " in artista_atual:
                partes = artista_atual.split(", ")
                ultimo_pedaco = partes[-1].strip()
                
                # Se o pedaço for curto (<= 3 letras) ou parecer incompleto
                if len(ultimo_pedaco) <= 3: 
                    melhor_candidato = None
                    maior_frequencia = 0
                    
                    for conhecido, freq in contador_artistas.items():
                        # Se o artista conhecido começa com esse pedaço (ex: "Som do Monte" começa com "So")
                        if conhecido.startswith(ultimo_pedaco) and conhecido != ultimo_pedaco:
                            if freq > maior_frequencia:
                                melhor_candidato = conhecido
                                maior_frequencia = freq
                    
                    if melhor_candidato:
                        partes[-1] = melhor_candidato
                        novo_artista = ", ".join(partes)
                        changed = True
                        # print(f"   🤖 Inferido: '...{ultimo_pedaco}' -> '{melhor_candidato}'")

            # SALVA SE HOUVE MUDANÇA
            if changed and novo_artista != artista_atual:
                nm = meta.copy()
                nm['artista'] = novo_artista
                doc_atual = documents[i]
                novo_doc = doc_atual.replace(artista_atual, novo_artista)
                
                self.collection.update(ids=[ids[i]], metadatas=[nm], documents=[novo_doc])
                print(f"   ✏️  Corrigido: '{artista_atual}' -> '{novo_artista}'")
                count += 1

        self.log(f"Correção de nomes finalizada. {count} registros ajustados.")

    def aplicar_patch_manual(self):
        if not self.collection: return
        self.log("🚑 Aplicando Patch Manual (Anos e Gêneros Faltantes)...")
        
        # 1. Correção de ANOS (Baseado no seu log de erro)
        CORRECAO_ANO = {
            # Trap / Funk
            "Papi": "2020",
            "Não Me Sinto Mal Mais": "2019",
            "Porsche": "2020",
            "Híbrido": "2021",
            "Oh Nega": "2016",
            "Loucaça": "2017",
            "M4": "2021",
            "Poesia Acústica #7": "2019",
            "Cake": "2022",
            "Espinafre": "2022",
            "Party": "2022",
            "Conexões de Máfia": "2023",
            
            # Eletrônica / Pop
            "Like I Do": "2018",
            "My Life Is Going On": "2018",
            "Keep It Mello": "2016",
            "Lalala": "2019",
            "Sucker": "2024",
            
            # Rock / Clássicos BR
            "Na Linha do Tempo": "2013",
            "Só Os Loucos Sabem": "2010",
            "Sutilmente": "2008",
            "Anna Júlia": "1999",
            "Meu Cemitério": "2014",
            
            # Rock Internacional
            "Youth of the Nation": "2001",
            "Blood's Thicker Than Water": "2021",
            
            # Gospel
            "Banquete": "2019",
            "Pela Manhã Te Buscarei": "2011"
        }

        # 2. Correção de GÊNERO (Força 'Católica/Worship' para quem estiver sem)
        ARTISTAS_WORSHIP = ["Frei Gilson", "Som do Monte", "Bruna Ramos", "Frei Silvio", "Juninho Cassimiro", "Lohane Dias"]

        count_ano = 0
        count_genero = 0
        
        dados = self.collection.get()
        ids = dados['ids']
        metadatas = dados['metadatas']
        documents = dados['documents']

        for i, meta in enumerate(metadatas):
            changed = False
            nm = meta.copy()
            doc_novo = documents[i]
            
            musica = meta.get('musica', '')
            artista = meta.get('artista', '')
            
            # --- CORREÇÃO DE ANO ---
            for trecho_musica, ano_correto in CORRECAO_ANO.items():
                if trecho_musica.lower() in musica.lower():
                    if str(nm.get('ano')) != ano_correto:
                        nm['ano'] = ano_correto
                        if f"Ano: {ano_correto}" not in doc_novo:
                            doc_novo += f" Ano: {ano_correto}."
                        changed = True
                        count_ano += 1
                        break 

            # --- CORREÇÃO DE GÊNERO ---
            if not nm.get('genero') or nm.get('genero') == 'Música' or nm.get('genero') == 'Desconhecido':
                if any(art.lower() in artista.lower() for art in ARTISTAS_WORSHIP):
                    nm['genero'] = "Católica/Worship"
                    if "Católica/Worship" not in doc_novo:
                        doc_novo += " Gênero: Católica/Worship."
                    changed = True
                    count_genero += 1

            if changed:
                self.collection.update(ids=[ids[i]], metadatas=[nm], documents=[doc_novo])
                # print(f"   🔧 Atualizado: {musica[:20]}...")

        self.log(f"Patch Finalizado: {count_ano} anos corrigidos | {count_genero} gêneros definidos.")