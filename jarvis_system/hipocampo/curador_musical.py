import os
import sys
import time
import requests
import webbrowser
import json
from datetime import datetime

# Garante acesso aos módulos internos
sys.path.append(os.getcwd())
from jarvis_system.hipocampo.memoria import memoria

class CuradorMusical:
    def __init__(self):
        self.collection = None
        if memoria._conectar():
            self.collection = memoria.collection

    def _log(self, msg):
        print(f"   [CURADOR] {msg}")

    # --- HABILIDADE 1: DIAGNÓSTICO E RELATÓRIO ---
    def gerar_relatorio(self):
        print("\n📊 [CURADOR] Gerando Relatório 'biblioteca_musical.txt'...")
        dados = self.collection.get()
        metadatas = dados['metadatas']
        
        # Ordena por Artista -> Música
        metadatas_ordenados = sorted(metadatas, key=lambda x: (x.get('artista', 'ZZZ'), x.get('musica', 'ZZZ')))
        
        nome_arquivo = "biblioteca_musical.txt"
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            f.write("="*120 + "\n")
            f.write(f"{'MÚSICA':<40} | {'ARTISTA':<30} | {'GÊNERO':<20} | {'ANO':<6}\n")
            f.write("="*120 + "\n")
            for meta in metadatas_ordenados:
                m = str(meta.get('musica',''))[:38]
                a = str(meta.get('artista',''))[:28]
                g = str(meta.get('genero',''))[:18]
                y = str(meta.get('ano','-'))[:4]
                f.write(f"{m:<40} | {a:<30} | {g:<20} | {y:<6}\n")
        
        self._log(f"Arquivo gerado com sucesso: {nome_arquivo}")
        self._log(f"Total de faixas indexadas: {len(metadatas)}")

    # --- HABILIDADE 2: ENRIQUECIMENTO (ITUNES API) ---
    def buscar_anos_faltantes(self):
        print("\n⏳ [CURADOR] Buscando anos e capas na Apple Music/iTunes...")
        dados = self.collection.get()
        ids = dados['ids']
        metadatas = dados['metadatas']
        
        count = 0
        for i, meta in enumerate(metadatas):
            # Só busca se não tiver ano ou for inválido
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
                        
                        # Atualiza documento textual para busca
                        doc_antigo = dados['documents'][i]
                        doc_novo = f"{doc_antigo} Ano: {ano}."
                        
                        self.collection.update(ids=[ids[i]], metadatas=[novo_meta], documents=[doc_novo])
                        print(f"   ✅ {musica}: {ano}")
                        count += 1
                        time.sleep(0.3) # Evita bloqueio da API
                except: pass
        self._log(f"Processo finalizado. {count} músicas enriquecidas via API.")

    # --- HABILIDADE 3: PATCH MANUAL DE EMERGÊNCIA ---
    def aplicar_patch_manual(self):
        """Corrige manualmente as músicas que a API não encontrou (Matuê, Virais, etc.)"""
        print("\n🚑 [CURADOR] Aplicando Patch Manual de Datas (Matuê, Virais, Trilhas)...")
        
        # Gabarito extraído da sua lista de erros
        GABARITO = {
            "Sucker (from the series Arcane League of Legends)": "2024",
            "Problemas de um Milionário": "2023",
            "Edit do Chico Oficial": "2023",
            "De 10 Mulher 11 É Maluca": "2023",
            "Aquariano Nato": "2023",
            "MONTAGEM CORAL (feat. Mc Cyclope)": "2023",
            "Tenho que Me Decidir": "2023",
            "Lancha No Mar": "2022",
            "Sessão de Cria 2: Beroba Freestyle": "2022",
            "Avisa Minha Mãe": "2021",
            "Eu Volto (8D) - Remix": "2021",
            "f a s h i o n w e e k": "2020",
            "Não Manda Áudio": "2021",
            "* da Anitta": "2022",
            "Conexões de Máfia (feat. Rich The Kid)": "2023",
            "Euro$tep": "2024",
            "Zoom!": "2020",
            "DANCE!": "2021",
            "Bunny Girl": "2020",
            "Shakira!": "2020",
            "Mustang Preto": "2021",
            "M4": "2021",
            "Não Me Sinto Mal Mais": "2019",
            "Porsche": "2020",
            "Híbrido": "2021",
            "777-666": "2020",
            "Oh Nega": "2016",
            "Loucaça": "2017",
            "Anjos na Rebeldia": "2017",
            "Vagalumes": "2012",
            "Like I Do": "2018",
            "Tenta Vir - Acústico": "2017",
            "My Life Is Going On": "2018",
            "Keep It Mello": "2016",
            "REI TUÊ": "2020",
            "Cemitério": "2013", # Provável "Meu Cemitério"
            "ÍCONE FASHION": "2020",
            "AUTOBAHN": "2023",
            "NANANANA": "2020",
            "FACAS E MACHADOS": "2024",
            "ALTERADO": "2024",
            "PENSAMENTOS PERIGOSOS": "2024",
            "BACKSTAGE": "2024",
            "TODAS AS LUZES": "2024",
            "OS MELHORES": "2024",
            "Armamento Russo": "2023",
            "BOLANDO UM PLANO": "2023",
            "100% MOLHO": "2023",
            "TRAPLIFE": "2023",
            "JUICY": "2023",
            "ACIMA DAS NUVENS": "2023",
            "JOGO ELA NO JATINHO": "2023",
            "SONHOS": "2023",
            "MIGOS": "2023",
            "BÁSICO": "2023",
            "BASEADO IGNORANTE": "2023",
            "TUDO BEM": "2023",
            "NOITE PERFEITA": "2023",
            "OH MY BABY": "2023",
            "PRIMAVERA": "2023",
            "RAGE": "2023",
            "MAZE BANK": "2023",
            "Poesia Acústica 12": "2022",
            "Drip da Roça": "2022",
            "Saturno": "2021",
            "Poesia Acústica #7": "2019",
            "Celine": "2020",
            "Cake": "2022",
            "Nunca Duvide de um Mano": "2023",
            "Espinafre": "2022",
            "Bandana 2": "2022",
            "Savana": "2022",
            "PARTY": "2022",
            "Mônaco Freestyle": "2022",
            "MEU MUNDO": "2022",
            "Desconhecida": "2006",
            "Suíte 14": "2014",
            "Blood's Thicker Than Water": "2022",
            "Na Linha do Tempo": "2012",
            "Só Os Loucos Sabem": "2010",
            "Sutilmente": "2008",
            "Anna Júlia": "2017",
            "Youth of the Nation": "2001",
            "Shepherd of Fire": "2013",
            "Lalala": "2019",
            "By the Sword": "2020",
            "Moshpit": "2023",
            "FUCK IT": "2021",
            "2 FAST 2 FURIOUS": "2021",
            "Hanglo": "2020",
            "A Little Of This": "1995",
            "MMM": "2021",
            "8 O 8": "2021",
            "Soda Pop": "2021",
            "Candy Paint": "2017",
            "Miss Me - Slowed + Reverb": "2021",
            "Banquete": "2019",
            "Pela Manhã Te Buscarei": "2011",
            "The Hills of Aberfeldy": "1996",
            "Baby One More Time": "2017"
        }
        
        count = 0
        for termo, ano_correto in GABARITO.items():
            # Busca aproximada pelo nome da música
            res = self.collection.query(query_texts=[termo], n_results=1)
            if res['ids'] and res['ids'][0]:
                meta = res['metadatas'][0][0]
                doc_id = res['ids'][0][0]
                doc_text = res['documents'][0][0]
                
                # Verifica se é a música certa (contém parte do nome)
                if termo.lower() in meta['musica'].lower() or termo.split('(')[0].strip().lower() in meta['musica'].lower():
                    if str(meta.get('ano')) != ano_correto:
                        nm = meta.copy()
                        nm['ano'] = ano_correto
                        nd = doc_text.replace("Ano: -", f"Ano: {ano_correto}")
                        if f"Ano: {ano_correto}" not in nd: nd += f" Ano: {ano_correto}."
                        
                        self.collection.update(ids=[doc_id], metadatas=[nm], documents=[nd])
                        print(f"   🔧 Corrigido: {meta['musica']} -> {ano_correto}")
                        count += 1
        
        self._log(f"Patch aplicado em {count} faixas.")

    # --- HABILIDADE 4: CORREÇÃO DE GÊNEROS ---
    def refinar_generos(self):
        print("\n💎 [CURADOR] Refinando Gêneros Musicais (Matuê, Safadão, etc)...")
        MAPA = {
            "Forró/Piseiro": ["Wesley Safadão", "Xand Avião", "João Gomes", "NATTAN", "Barões", "Felipe Amorim", "Tarcísio", "Raí Saia Rodada", "Mari Fernandez", "Avine Vinny"],
            "Rock": ["Linkin Park", "Nirvana", "Red Hot", "System of a Down", "Evanescence", "Skank", "Charlie Brown", "Audioslave", "Foo Fighters", "Pearl Jam", "Three Days Grace", "Nickelback", "AC/DC", "Guns N"],
            "Hip-Hop/Rap": ["Eminem", "Drake", "Post Malone", "1Kilo", "Hungria", "Tupac", "50 Cent", "Snoop Dogg", "Jay-Z", "Kanye West", "Wiz Khalifa", "Black Eyed Peas", "Kendrick Lamar", "Travis Scott", "Coolio"],
            "Trap": ["Matuê", "Teto", "WIU", "Brandão85", "Sidoka", "Veigh", "KayBlack", "MC Cabelinho", "Orochi"],
            "Pop": ["Justin Bieber", "Coldplay", "Maroon 5", "Imagine Dragons", "Ed Sheeran", "Bruno Mars", "Dua Lipa", "Rihanna", "Lady Gaga"],
            "Católica/Worship": ["Frei Gilson", "Padre", "Worship", "Colo de Deus", "Fernandinho", "Casa Worship", "Gabriela Rocha", "Morada", "Rosa de Saron", "Thiago Brado"],
            "Reggae/Vibe": ["Natiruts", "Maneva", "Melim", "Lagum", "Vitor Kley", "Armandinho"],
            "Eletrônica": ["Alok", "Vintage Culture", "Avicii", "David Guetta", "Calvin Harris", "Martin Garrix", "Tiësto", "Marshmello"]
        }

        dados = self.collection.get()
        ids = dados['ids']
        metadatas = dados['metadatas']
        count = 0

        for i, meta in enumerate(metadatas):
            artista = meta.get('artista', '')
            genero_atual = meta.get('genero', '')
            
            for gen_alvo, lista in MAPA.items():
                if any(x.lower() in artista.lower() for x in lista):
                    if genero_atual != gen_alvo:
                        nm = meta.copy()
                        nm['genero'] = gen_alvo
                        doc = dados['documents'][i].replace(f"Gênero: {genero_atual}", f"Gênero: {gen_alvo}")
                        if gen_alvo not in doc: doc += f" Gênero: {gen_alvo}."
                        
                        self.collection.update(ids=[ids[i]], metadatas=[nm], documents=[doc])
                        print(f"   🎸 {artista}: {genero_atual} -> {gen_alvo}")
                        count += 1
                    break
        self._log(f"{count} gêneros reclassificados.")

    # --- HABILIDADE 5: DJ ---
    def tocar_dj(self, comando):
        print(f"\n🎧 [DJ JARVIS] Buscando: '{comando}'")
        res = self.collection.query(query_texts=[comando], n_results=1)
        if res['ids'] and res['ids'][0]:
            meta = res['metadatas'][0][0]
            print(f"   💿 Tocando: {meta.get('musica')} - {meta.get('artista')} ({meta.get('ano', '')})")
            if meta.get('preview_url'): webbrowser.open(meta.get('preview_url'))
            elif meta.get('capa_url'): webbrowser.open(meta.get('capa_url'))
        else:
            self._log("Nada encontrado.")

    # --- HABILIDADE 6: FAXINA DE LIXO ---
    def remover_lixo(self):
        print("\n🧹 [CURADOR] Removendo registros inválidos...")
        lixo = self.collection.get(where={"artista": "Videoclipe"})
        if lixo['ids']:
            self.collection.delete(ids=lixo['ids'])
            self._log(f"🗑️ Removidos {len(lixo['ids'])} itens 'Videoclipe'.")
        else:
            self._log("Nenhum lixo crítico encontrado.")