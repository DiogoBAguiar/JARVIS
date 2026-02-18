class MusicReporter:
    def __init__(self, collection, logger_func):
        self.collection = collection
        self.log = logger_func

    def gerar_relatorio(self):
        if not self.collection:
            self.log("Memória desconectada.")
            return

        self.log("📊 Gerando Relatório 'biblioteca_musical.txt'...")
        dados = self.collection.get()
        metadatas = dados['metadatas']
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
        
        self.log(f"Arquivo gerado: {nome_arquivo} ({len(metadatas)} faixas)")