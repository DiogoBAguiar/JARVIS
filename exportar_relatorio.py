import os
import sys

# Garante raiz do projeto
sys.path.append(os.getcwd())
from jarvis_system.hipocampo.memoria import memoria

def truncar(texto, limite):
    """Corta textos muito longos para não quebrar a tabela"""
    texto = str(texto)
    if len(texto) > limite:
        return texto[:limite-3] + "..."
    return texto

def exportar_tabela():
    print("📊 GERANDO RELATÓRIO EM TABELA...")
    
    if not memoria._conectar(): return
    collection = memoria.collection
    
    # 1. Pega tudo
    dados = collection.get()
    metadatas = dados['metadatas']
    
    if not metadatas:
        print("❌ Banco vazio.")
        return

    # 2. Ordena por Artista -> Música
    print("   🔄 Ordenando dados...")
    metadatas_ordenados = sorted(metadatas, key=lambda x: (x.get('artista', 'ZZZ'), x.get('musica', 'ZZZ')))

    # 3. Configuração das Colunas (Largura fixa)
    col_musica = 40
    col_artista = 30
    col_genero = 20
    col_album = 30
    col_ano = 6

    nome_arquivo = "biblioteca_musical.txt"

    print(f"   💾 Escrevendo em '{nome_arquivo}'...")
    
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        # Cabeçalho
        titulo = " RELATÓRIO GERAL - MEMÓRIA MUSICAL J.A.R.V.I.S "
        f.write("=" * 135 + "\n")
        f.write(f"{titulo:^135}\n")
        f.write("=" * 135 + "\n\n")

        # Topo da Tabela
        header = (
            f"{'MÚSICA':<{col_musica}} | "
            f"{'ARTISTA':<{col_artista}} | "
            f"{'GÊNERO':<{col_genero}} | "
            f"{'ÁLBUM':<{col_album}} | "
            f"{'ANO':<{col_ano}}"
        )
        f.write(header + "\n")
        f.write("-" * 135 + "\n")

        # Linhas
        for meta in metadatas_ordenados:
            musica = truncar(meta.get('musica', '-'), col_musica)
            artista = truncar(meta.get('artista', '-'), col_artista)
            genero = truncar(meta.get('genero', '-'), col_genero)
            album = truncar(meta.get('album', '-'), col_album)
            ano = str(meta.get('ano', '-'))[:4]

            linha = (
                f"{musica:<{col_musica}} | "
                f"{artista:<{col_artista}} | "
                f"{genero:<{col_genero}} | "
                f"{album:<{col_album}} | "
                f"{ano:<{col_ano}}"
            )
            f.write(linha + "\n")

        # Rodapé Estatístico
        f.write("\n" + "=" * 135 + "\n")
        f.write(f" TOTAL DE FAIXAS: {len(metadatas)}\n")
        f.write("=" * 135 + "\n")

    print(f"✅ Sucesso! Abra o arquivo '{nome_arquivo}' para ver sua coleção.")

if __name__ == "__main__":
    exportar_tabela()