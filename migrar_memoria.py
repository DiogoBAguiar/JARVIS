import os
import sys
import random
import webbrowser
import time

# Garante raiz do projeto
sys.path.append(os.getcwd())
from jarvis_system.hipocampo.memoria import memoria

def tocar_musica(comando):
    print(f"\n🎧 J.A.R.V.I.S. Processando pedido: '{comando}'...")
    
    if not memoria._conectar(): 
        print("❌ Erro de conexão com a memória.")
        return

    collection = memoria.collection
    termo = comando.lower()
    
    # --- 1. INTELIGÊNCIA DE DJ (Roteamento) ---
    filtro = {}
    
    # Detecta Gêneros
    if "sertanejo" in termo: filtro["genero"] = "Sertanejo"
    elif "rock" in termo: filtro["genero"] = "Rock"
    elif "trap" in termo: filtro["genero"] = "Trap"
    elif "rap" in termo or "hip" in termo: filtro["genero"] = "Hip-Hop/Rap"
    elif "eletr" in termo or "dance" in termo: filtro["genero"] = "Eletrônica"
    elif "forr" in termo or "pisadinha" in termo: filtro["genero"] = "Forró/Piseiro"
    elif "lol" in termo or "league" in termo or "jogar" in termo: 
        filtro["genero"] = "Soundtrack/Game"
    
    # Detecta Artistas Específicos (Busca simples no texto)
    if not filtro:
        # Se não pediu gênero, assume que é uma busca por artista/nome
        print(f"   🔍 Buscando por nome/artista: '{comando}'")
        resultados = collection.query(query_texts=[comando], n_results=10)
        
        if not resultados['ids'] or not resultados['ids'][0]:
            print("   ❌ Não encontrei nada parecido na sua biblioteca.")
            return
            
        # Pega a melhor correspondência
        meta = resultados['metadatas'][0][0]
        
    else:
        # Se pediu gênero, pega aleatório daquele gênero
        print(f"   🎲 Selecionando um {filtro['genero']} aleatório para você...")
        resultados = collection.get(where=filtro)
        
        qtd = len(resultados['ids'])
        if qtd == 0:
            print(f"   ⚠️ Nenhuma música encontrada no gênero {filtro['genero']}.")
            return
            
        idx_rand = random.randint(0, qtd - 1)
        meta = resultados['metadatas'][idx_rand]

    # --- 2. DISPLAY DO PLAYER ---
    musica = meta.get('musica', 'Desconhecida')
    artista = meta.get('artista', 'Desconhecido')
    genero = meta.get('genero', 'Indefinido')
    album = meta.get('album', 'Single')
    ano = meta.get('ano', '')
    capa = meta.get('capa_url')
    preview = meta.get('preview_url')
    
    print("\n" + "="*50)
    print(f"💿 TOCANDO AGORA 💿")
    print("="*50)
    print(f"🎵 Música:  {musica}")
    print(f"🎤 Artista: {artista}")
    print(f"🎹 Gênero:  {genero}")
    print(f"💿 Álbum:   {album} ({ano})")
    print("="*50)
    
    # --- 3. AÇÃO REAL ---
    # Abre a capa do álbum para dar um efeito visual "Now Playing"
    if capa:
        print("   🖼️ Exibindo capa do álbum...")
        webbrowser.open(capa)
    else:
        print("   (Sem capa disponível)")

    # Se tiver preview do iTunes, toca (abre no navegador)
    if preview:
        print("   🔊 Abrindo áudio...")
        # Pequeno delay para não abrir tudo de uma vez
        time.sleep(1) 
        webbrowser.open(preview)
    else:
        print("   ⚠️ Link de áudio não disponível (apenas metadados).")

if __name__ == "__main__":
    while True:
        print("\n" + "-"*50)
        pedido = input("🎤 Peça uma música (ou 'sair'): ")
        if pedido.lower() in ['sair', 'exit']: break
        
        tocar_musica(pedido)