import os
import sys
import collections
import re # <--- Importante para separar os nomes
from tabulate import tabulate

# --- AJUSTE DE PATH ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Importa a Memória
try:
    from jarvis_system.hipocampo.memoria import memoria
except ImportError:
    print("❌ Erro: Não foi possível importar o módulo de memória.")
    sys.exit(1)

def limpar_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

class DatabaseAnalyzer:
    def __init__(self):
        print("🔌 Conectando ao Hipocampo...")
        if not memoria or not memoria._conectar():
            print("❌ Erro: Falha na conexão com o banco de dados.")
            self.collection = None
        else:
            self.collection = memoria.collection

    def iniciar(self):
        if not self.collection: return

        while True:
            limpar_terminal()
            count = self.collection.count()
            print("📊 J.A.R.V.I.S. - ANALISADOR DE DADOS (V2)")
            print("==============================================")
            print(f"📦 Total de Registros: {count}")
            print("==============================================")
            print("1. 🏆 Top Artistas Individuais (Separa Feats)")
            print("2. 🔍 Inspecionar Dados (Amostragem)")
            print("3. 🧪 Testar Busca Semântica")
            print("4. 📋 Verificar Integridade")
            print("5. 🗑️  Deletar Item por ID")
            print("0. 🔙 Sair")
            print("==============================================")
            
            opt = input("Escolha uma opção: ")

            if opt == "1": self.mostrar_estatisticas()
            elif opt == "2": self.mostrar_amostra()
            elif opt == "3": self.testar_busca()
            elif opt == "4": self.verificar_metadados()
            elif opt == "5": self.deletar_item()
            elif opt == "0": break

    def mostrar_estatisticas(self):
        print("\n⏳ Processando e separando artistas... (Aguarde)")
        data = self.collection.get()
        metadatas = data['metadatas']
        
        artistas_individuais = []
        generos = []

        for meta in metadatas:
            # GÊNEROS (Simples)
            if meta.get('genero'): 
                generos.append(meta['genero'])

            # ARTISTAS (Lógica Inteligente de Separação)
            raw_artist = meta.get('artista', '')
            if raw_artist:
                # Quebra a string onde tiver vírgula, & ou "feat"
                # Ex: "Frei Gilson, Bruna Ramos" -> ["Frei Gilson", "Bruna Ramos"]
                partes = re.split(r',|&| feat\. | ft\. ', raw_artist, flags=re.IGNORECASE)
                
                for p in partes:
                    nome_limpo = p.strip()
                    # Filtra lixo (strings vazias ou muito curtas que não sejam siglas)
                    if len(nome_limpo) > 1:
                        artistas_individuais.append(nome_limpo)

        print("\n🏆 TOP 20 ARTISTAS INDIVIDUAIS (Contagem Real):")
        # Agora o Frei Gilson vai somar todas as aparições!
        self._print_top_table(artistas_individuais, 20, "Artista")

        print("\n🎸 DISTRIBUIÇÃO DE GÊNEROS:")
        self._print_top_table(generos, 20, "Gênero")
        
        input("\n[Enter] para voltar...")

    def _print_top_table(self, data_list, limit, label):
        counter = collections.Counter(data_list)
        common = counter.most_common(limit)
        table = [[i+1, k, v] for i, (k, v) in enumerate(common)]
        print(tabulate(table, headers=["#", label, "Participações"], tablefmt="fancy_grid"))

    def mostrar_amostra(self):
        try:
            n = int(input("\nQuantos itens deseja ver? (Padrão 10): ") or 10)
        except: n = 10
        
        results = self.collection.get(limit=n)
        
        table = []
        for i, meta in enumerate(results['metadatas']):
            id_ = results['ids'][i]
            musica = (meta.get('musica', 'N/A')[:30] + '..') if len(meta.get('musica', '')) > 30 else meta.get('musica', 'N/A')
            artista = (meta.get('artista', 'N/A')[:25] + '..') if len(meta.get('artista', '')) > 25 else meta.get('artista', 'N/A')
            
            table.append([
                id_[:8],
                musica,
                artista,
                meta.get('genero', '-'),
                meta.get('ano', '-')
            ])
        
        print(f"\n🔍 Últimos {len(table)} itens adicionados:")
        print(tabulate(table, headers=["ID", "Música", "Artista (Raw)", "Gênero", "Ano"], tablefmt="grid"))
        input("\n[Enter] para voltar...")

    def testar_busca(self):
        query = input("\n🧠 Digite o termo para busca (Ex: 'musica triste'): ")
        if not query: return

        k = 5
        results = self.collection.query(query_texts=[query], n_results=k)
        
        print(f"\n🎯 Resultados para: '{query}'")
        print("-" * 60)
        
        ids = results['ids'][0]
        # dists = results['distances'][0] # Opcional
        metas = results['metadatas'][0]
        docs = results['documents'][0]

        for i in range(len(ids)):
            print(f"#{i+1}")
            print(f"   🎵 {metas[i].get('musica')} - {metas[i].get('artista')}")
            print(f"   🏷️  {metas[i].get('genero')} | {metas[i].get('ano')}")
            print(f"   📄 Doc: {docs[i]}")
            print("-" * 60)
        
        input("\n[Enter] para voltar...")

    def verificar_metadados(self):
        print("\n📋 Verificando consistência...")
        data = self.collection.get()
        metadatas = data['metadatas']
        
        campos_esperados = {'musica', 'artista', 'genero', 'ano', 'album'}
        problemas = 0
        
        for i, meta in enumerate(metadatas):
            chaves = set(meta.keys())
            faltantes = campos_esperados - chaves
            if faltantes:
                print(f"⚠️  {data['ids'][i]} incompleto. Faltam: {faltantes}")
                problemas += 1
        
        if problemas == 0: print("✅ Tudo 100%.")
        else: print(f"❌ {problemas} erros encontrados.")
        input("\n[Enter] para voltar...")

    def deletar_item(self):
        id_alvo = input("\n🗑️  ID para deletar: ")
        if not id_alvo: return
        
        if input("Confirma? (s/n): ").lower() == 's':
            try:
                self.collection.delete(ids=[id_alvo])
                print("✅ Deletado.")
            except Exception as e:
                print(f"Erro: {e}")
        input("\n[Enter] para voltar...")

if __name__ == "__main__":
    app = DatabaseAnalyzer()
    app.iniciar()