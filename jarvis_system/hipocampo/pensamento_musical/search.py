import re
from difflib import SequenceMatcher

class MusicSearchEngine:
    def __init__(self, collection, logger_func):
        self.collection = collection
        self.log = logger_func

    def existe_artista(self, nome: str) -> bool:
        """Verifica existência exata ou substring simples."""
        if not self.collection: return False
        try:
            # Busca Exata
            if self.collection.get(where={"artista": nome}, limit=1)['ids']: return True
            # Busca Parcial
            res = self.collection.query(query_texts=[nome], n_results=5)
            if res['metadatas'] and res['metadatas'][0]:
                for meta in res['metadatas'][0]:
                    if nome.lower() in meta.get('artista', '').lower(): return True
            return False
        except: return False

    def buscar_vetorial(self, query: str, top_k: int = 1) -> list:
        # ... (código existente da busca vetorial) ...
        if not self.collection: return []
        try:
            resultados = self.collection.query(query_texts=[query], n_results=top_k)
            respostas = []
            if resultados['ids'] and resultados['ids'][0]:
                for meta in resultados['metadatas'][0]:
                    musica = meta.get('musica', 'Desconhecida')
                    artista = meta.get('artista', 'Desconhecido')
                    respostas.append(f"{musica} de {artista}")
            return respostas
        except: return []

    # --- NOVO: CORREÇÃO INTELIGENTE ---
    def sugerir_correcao(self, termo_errado: str, cutoff=0.6) -> str:
        """
        Recebe 'freio gil som' e retorna 'Frei Gilson' se a similaridade for alta.
        """
        if not self.collection: return None
        
        # 1. Coleta todos os artistas únicos do banco
        dados = self.collection.get()
        todos_artistas = set()
        
        for meta in dados['metadatas']:
            raw = meta.get('artista', '')
            # Separa os artistas para comparar individualmente
            # Ex: "Frei Gilson, Som do Monte" vira ["Frei Gilson", "Som do Monte"]
            partes = re.split(r',|&| feat\. | ft\. ', raw, flags=re.IGNORECASE)
            for p in partes:
                limpo = p.strip()
                if len(limpo) > 2: todos_artistas.add(limpo)

        # 2. Encontra o melhor match estatístico
        melhor_candidato = None
        melhor_score = 0.0

        termo_lower = termo_errado.lower()

        for artista in todos_artistas:
            artista_lower = artista.lower()
            
            # Calcula similaridade (0.0 a 1.0)
            score = SequenceMatcher(None, termo_lower, artista_lower).ratio()
            
            if score > melhor_score and score >= cutoff:
                melhor_score = score
                melhor_candidato = artista

        if melhor_candidato:
            self.log(f"🧠 Correção aplicada: '{termo_errado}' -> '{melhor_candidato}' ({int(melhor_score*100)}% similar)")
            return melhor_candidato
            
        return None