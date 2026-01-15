import os
import sys
import collections
import re
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
        
        # --- DIAGNÓSTICO FÍSICO (Herdado do antigo gerenciador) ---
        if hasattr(memoria, 'db_path') and os.path.exists(memoria.db_path):
            arquivos = os.listdir(memoria.db_path)
            if "chroma.sqlite3" in arquivos:
                print(f"   ✅ Arquivo físico do banco encontrado em: {memoria.db_path}")
            else:
                print(f"   ⚠️  Pasta existe, mas 'chroma.sqlite3' não encontrado.")
        
        if not memoria or not memoria._conectar():
            print("❌ Erro: Falha na conexão lógica com o ChromaDB.")
            self.collection = None
        else:
            self.collection = memoria.collection

    def iniciar(self):
        if not self.collection: return

        while True:
            limpar_terminal()
            count = self.collection.count()
            print("📊 J.A.R.V.I.S. - ANALISADOR DE DADOS (V3 FINAL)")
            print("==============================================")
            print(f"📦 Total de Registros: {count}")
            print("==============================================")
            print("1. 🏆 Top Artistas (Individuais)")
            print("2. 🔍 Inspecionar Dados (Amostragem)")
            print("3. 🏷️  Estatísticas de Tags (Legacy)")
            print("4. 🧪 Testar Busca Semântica")
            print("5. 📋 Verificar Integridade")
            print("6. 🗑️  Deletar Item por ID")
            print("0. 🔙 Sair")
            print("==============================================")
            
            opt = input("Escolha uma opção: ")

            if opt == "1": self.mostrar_estatisticas()
            elif opt == "2": self.mostrar_amostra()
            elif opt == "3": self.mostrar_tags_legacy()
            elif opt == "4": self.testar_busca()
            elif opt == "5": self.verificar_metadados()
            elif opt == "6": self.deletar_item()
            elif opt == "0": break

    def mostrar_estatisticas(self):
        print("\n⏳ Processando e separando artistas...")
        data = self.collection.get()
        metadatas = data['metadatas']
        
        artistas_individuais = []
        generos = []

        for meta in metadatas:
            # GÊNEROS
            if meta.get('genero'): 
                generos.append(meta['genero'])

            # ARTISTAS (Separação Inteligente)
            raw_artist = meta.get('artista', '')
            if raw_artist:
                # Quebra a string onde tiver vírgula, & ou "feat"
                partes = re.split(r',|&| feat\. | ft\. ', raw_artist, flags=re.IGNORECASE)
                for p in partes:
                    nome_limpo = p.strip()
                    if len(nome_limpo) > 1:
                        artistas_individuais.append(nome_limpo)

        print("\n🏆 TOP 20 ARTISTAS INDIVIDUAIS:")
        self._print_top_table(artistas_individuais, 20, "Artista")

        print("\n🎸 DISTRIBUIÇÃO DE GÊNEROS:")
        self._print_top_table(generos, 20, "Gênero")
        
        input("\n[Enter] para voltar...")

    def _print_top_table(self, data_list, limit, label):
        counter = collections.Counter(data_list)
        common = counter.most_common(limit)
        table = [[i+1, k, v] for i, (k, v) in enumerate(common)]
        print(tabulate(table, headers=["#", label, "Qtd"], tablefmt="fancy_grid"))

    def mostrar_tags_legacy(self):
        print("\n📊 Analisando Tags (Contextos)...")
        data = self.collection.get()
        metadatas = data['metadatas']
        
        tags = []
        for meta in metadatas:
            t = meta.get('tags', 'sem_tag')
            tags.append(t)
            
        counter = collections.Counter(tags)
        table = [[k, v] for k, v in counter.most_common()]
        
        print(tabulate(table, headers=["Tag/Contexto", "Quantidade"], tablefmt="fancy_grid"))
        input("\n[Enter] para voltar...")

    def mostrar_amostra(self):
        try:
            n = int(input("\nQtd? (10): ") or 10)
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
        print(tabulate(table, headers=["ID", "Música", "Artista", "Gênero", "Ano"], tablefmt="grid"))
        input("\n[Enter] para voltar...")

    def testar_busca(self):
        query = input("\n🧠 Termo: ")
        if not query: return

        k = 5
        results = self.collection.query(query_texts=[query], n_results=k)
        
        for i in range(len(results['ids'][0])):
            m = results['metadatas'][0][i]
            print(f"#{i+1} {m.get('musica')} - {m.get('artista')} ({m.get('genero')})")
        
        input("\n[Enter] para voltar...")

    def verificar_metadados(self):
        print("\n📋 Verificando...")
        data = self.collection.get()
        campos = {'musica', 'artista', 'genero', 'ano'}
        prob = 0
        for i, m in enumerate(data['metadatas']):
            if campos - set(m.keys()):
                print(f"⚠️ {data['ids'][i]} incompleto.")
                prob += 1
        print(f"Fim. {prob} problemas.")
        input("\n[Enter] para voltar...")

    def deletar_item(self):
        id_alvo = input("\n🗑️  ID: ")
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