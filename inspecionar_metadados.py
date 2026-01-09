import os
import sys
from collections import Counter

# Garante raiz do projeto
sys.path.append(os.getcwd())

from jarvis_system.hipocampo.memoria import memoria

def auditoria_pos_faxina():
    print("🕵️‍♂️ AUDITORIA FINAL DO BANCO DE DADOS - J.A.R.V.I.S")
    print("=" * 60)
    
    if not memoria._conectar():
        print("❌ Falha na conexão com o Hipocampo.")
        return

    collection = memoria.collection
    
    # 1. Puxar TODOS os metadados (sem os documentos pesados) para estatística
    print("📊 Calculando estatísticas globais...")
    all_data = collection.get(include=['metadatas'])
    metadatas = all_data['metadatas']
    total = len(metadatas)
    
    if total == 0:
        print("📭 O Banco está vazio.")
        return

    # 2. Análise de Artistas e Gêneros
    artistas = [m.get('artista', 'Desconhecido') for m in metadatas]
    generos = [m.get('genero', 'Não Classificado') for m in metadatas]
    albuns = [m.get('album') for m in metadatas if m.get('album')] # Só conta se tiver álbum

    contagem_artistas = Counter(artistas)
    contagem_generos = Counter(generos)

    print(f"\n📈 RESUMO ESTATÍSTICO:")
    print(f"   • Total de Músicas: {total}")
    print(f"   • Artistas Únicos:  {len(contagem_artistas)}")
    print(f"   • Músicas com Álbum (Enriquecidas): {len(albuns)}")
    
    print("\n🏆 TOP 5 GÊNEROS:")
    for genero, qtd in contagem_generos.most_common(5):
        print(f"   - {genero}: {qtd}")

    # 3. Inspeção de Amostra (Os últimos 5 adicionados/modificados)
    print("\n" + "="*60)
    print("🔍 INSPEÇÃO VISUAL (Últimos 5 registros):")
    
    # Pega os 5 últimos
    amostra = collection.get(limit=5)
    
    for i in range(len(amostra['ids'])):
        meta = amostra['metadatas'][i]
        doc = amostra['documents'][i]
        
        print(f"\n🆔 ID: {amostra['ids'][i]}")
        print(f"   🎵 Música:  {meta.get('musica', 'N/A')}")
        print(f"   🎤 Artista: {meta.get('artista', 'N/A')}")
        print(f"   🎹 Gênero:  {meta.get('genero', 'N/A')}")
        
        # Mostra campos extras se existirem (do enriquecimento)
        if 'album' in meta:
            print(f"   💿 Álbum:   {meta['album']} ({meta.get('ano', '')})")
            print(f"   🖼️ Capa:    Sim (URL salva)")
        
        print(f"   📄 Doc Raw: {doc[:80]}...") # Mostra só o começo do texto

    # 4. Prova Real: Verificar se o LoL foi salvo
    print("\n" + "="*60)
    print("🎮 PROVA REAL (Busca Específica: 'League of Legends')")
    
    lol_results = collection.get(where={"artista": "League of Legends"})
    qtd_lol = len(lol_results['ids'])
    
    if qtd_lol > 0:
        print(f"✅ SUCESSO! Encontrei {qtd_lol} faixas oficiais de League of Legends.")
        print(f"   Exemplo: {lol_results['metadatas'][0]['musica']}")
    else:
        print("⚠️ ALERTA: Nenhuma faixa de League of Legends encontrada.")

    # 5. Prova Real: Verificar se ainda existe lixo
    lixo_results = collection.get(where={"artista": "Videoclipe"})
    if len(lixo_results['ids']) == 0:
        print("✅ LIMPEZA CONFIRMADA: Nenhum artista 'Videoclipe' restou.")
    else:
        print(f"⚠️ AINDA EXISTEM {len(lixo_results['ids'])} REGISTROS SUJOS.")

if __name__ == "__main__":
    auditoria_pos_faxina()