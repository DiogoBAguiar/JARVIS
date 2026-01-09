import os
import sys
from collections import Counter
from dotenv import load_dotenv

# Carrega ambiente
load_dotenv()
sys.path.append(os.getcwd())

from jarvis_system.hipocampo.memoria import memoria

def listar_artistas():
    print("📊 ANALISANDO BANCO DE DADOS...")
    
    if not memoria._conectar(): return
    
    # Pega apenas os metadados para ser mais rápido
    dados = memoria.collection.get(include=['metadatas'])
    metadatas = dados['metadatas']
    
    total_musicas = len(metadatas)
    lista_artistas = []

    # Extrai e normaliza os nomes
    for meta in metadatas:
        nome = meta.get('artista', 'Desconhecido')
        if nome:
            # Remove espaços extras nas pontas para evitar duplicatas bobas
            lista_artistas.append(nome.strip())
        else:
            lista_artistas.append("Desconhecido")

    # Conta a frequência
    contagem = Counter(lista_artistas)
    
    # Ordena alfabeticamente
    artistas_ordenados = sorted(contagem.items(), key=lambda x: x[0].lower())

    print(f"\n🎵 Total de Músicas: {total_musicas}")
    print(f"🎤 Total de Artistas Únicos: {len(artistas_ordenados)}")
    print("-" * 40)
    print(f"{'ARTISTA':<40} | {'QTD'}")
    print("-" * 40)

    # Imprime no terminal
    for artista, qtd in artistas_ordenados:
        print(f"{artista:<40} | {qtd}")

    # (Opcional) Salva em arquivo para facilitar a leitura
    with open("relatorio_artistas.txt", "w", encoding="utf-8") as f:
        f.write(f"RELATÓRIO DE ARTISTAS - {total_musicas} Músicas\n")
        f.write("="*50 + "\n")
        for artista, qtd in artistas_ordenados:
            f.write(f"{artista} ({qtd})\n")
    
    print("-" * 40)
    print("📝 Lista salva também em 'relatorio_artistas.txt'")

if __name__ == "__main__":
    listar_artistas()