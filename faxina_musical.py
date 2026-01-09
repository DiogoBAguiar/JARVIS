import os
import sys
import time
from dotenv import load_dotenv

# Carrega ambiente
load_dotenv()
sys.path.append(os.getcwd())

from jarvis_system.hipocampo.memoria import memoria

# --- REGRAS DE CORREÇÃO (Onde a IA errou) ---
# Se o artista for X, o gênero TEM que ser Y.
CORRECOES_POR_ARTISTA = {
    # Trap / Rap
    "matuê": "Trap", "wiu": "Trap", "teto": "Trap", "30praum": "Trap",
    "felipe ret": "Trap/Rap", "oro": "Trap", "orochi": "Trap", 
    "poze": "Funk/Trap", "l7nnon": "Rap/Funk", "djonga": "Rap", 
    "bk": "Rap", "tz da coronel": "Trap", "kayblack": "Trap", 
    "veigh": "Trap", "major rd": "Drill/Rap", "lil whind": "Trap",
    "1nonly": "Aesthetic Rap", "post malone": "Hip Hop/Pop", 
    "travis scott": "Hip Hop", "eminem": "Hip Hop",
    
    # Piseiro / Forró
    "joão gomes": "Piseiro", "tarcísio do acordeon": "Piseiro", 
    "vitor fernandes": "Piseiro", "felipe amorim": "Piseiro/Pop", 
    "nattan": "Forró/Pop", "mari fernandez": "Piseiro",
    
    # Funk
    "mc daniel": "Funk", "mc ryan sp": "Funk", "mc hariel": "Funk", 
    "mc kevin": "Funk", "mc paiva": "Funk",
    
    # Gospel / Religioso (Muitos caíram como Sertanejo)
    "padre marcelo rossi": "Católica", "padre fábio de melo": "Católica",
    "frei gilson": "Católica", "thiago brado": "Católica",
    "aline barros": "Gospel", "fernandinho": "Gospel", 
    "isadora pompeo": "Gospel", "casa worship": "Gospel",
    "morada": "Gospel", "diante do trono": "Gospel",
    
    # Pop Internacional (Correções pontuais)
    "michael bublé": "Jazz/Pop", "frank sinatra": "Jazz",
}

def executar_faxina():
    print("🧹 INICIANDO FAXINA NOS METADADOS...")
    
    if not memoria._conectar(): return
    
    dados = memoria.collection.get()
    ids = dados['ids']
    metadatas = dados['metadatas']
    documents = dados['documents']
    
    total = len(ids)
    corrigidos = 0

    for i, meta in enumerate(metadatas):
        artista = meta.get('artista', '').lower()
        musica = meta.get('musica', '')
        genero_atual = meta.get('genero', '')
        
        novo_genero = None

        # 1. Verifica correção por Artista
        for artista_chave, genero_correto in CORRECOES_POR_ARTISTA.items():
            if artista_chave in artista:
                # Só corrige se estiver diferente ou genérico demais
                if genero_atual != genero_correto:
                    novo_genero = genero_correto
                break
        
        # 2. Correção de "Sertanejo" em faixas internacionais óbvias (Michael Bublé, etc)
        # Se não caiu na regra acima, mas é Sertanejo e o título é em inglês... suspeito.
        if not novo_genero and "sertanejo" in genero_atual.lower():
            # Lógica simples: Se o artista é internacional conhecido, muda pra Pop
            internacionais = ["ed sheeran", "maroon 5", "coldplay", "imagine dragons", "bruno mars", "james bay", "shawn mendes"]
            for gringo in internacionais:
                if gringo in artista:
                    novo_genero = "Pop"
                    break

        # SE HOUVER MUDANÇA, ATUALIZA
        if novo_genero:
            print(f"🔧 Corrigindo [{i}]: {artista} | De '{genero_atual}' para '{novo_genero}'")
            
            meta_atualizada = meta.copy()
            meta_atualizada['genero'] = novo_genero
            
            # Atualiza também o documento de texto para busca
            doc_atualizado = documents[i].replace(f"Gênero: {genero_atual}", f"Gênero: {novo_genero}")
            
            memoria.collection.upsert(
                ids=[ids[i]],
                metadatas=[meta_atualizada],
                documents=[doc_atualizado]
            )
            corrigidos += 1
            # Pequeno delay para não travar IO se for muita coisa
            if corrigidos % 10 == 0: time.sleep(0.1)

    print(f"\n✨ Faxina Concluída! {corrigidos} registros foram corrigidos.")

if __name__ == "__main__":
    executar_faxina()