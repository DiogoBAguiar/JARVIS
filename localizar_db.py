import os

def localizar_bancos():
    print("🔎 Iniciando busca global por bancos de dados ChromaDB...")
    raiz = os.getcwd()
    encontrados = []

    for diretorio, subpastas, arquivos in os.walk(raiz):
        if "chroma.sqlite3" in arquivos:
            caminho_completo = os.path.join(diretorio, "chroma.sqlite3")
            tamanho = os.path.getsize(caminho_completo) / 1024  # KB
            encontrados.append((caminho_completo, tamanho))

    if not encontrados:
        print("❌ Nenhum arquivo 'chroma.sqlite3' encontrado no projeto.")
        return

    print(f"\n✅ Foram encontrados {len(encontrados)} arquivos de banco:")
    print(f"{'Caminho':<60} | {'Tamanho (KB)':<15}")
    print("-" * 80)
    for caminho, tam in encontrados:
        print(f"{caminho:<60} | {tam:>10.2f} KB")
    
    print("\n💡 DICA: O banco com as 887 músicas deve ter o MAIOR tamanho (provavelmente > 500 KB).")

if __name__ == "__main__":
    localizar_bancos()