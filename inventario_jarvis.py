import os

# Caminho onde os áudios estão salvos
DIRETORIO_BANCO = os.path.join("jarvis_system", "area_broca", "voice_bank_fish")

def listar_estoque():
    print("\n" + "="*50)
    print("📊  INVENTÁRIO DE VOCABULÁRIO J.A.R.V.I.S.")
    print("="*50)
    print(f"📂 Diretório: {DIRETORIO_BANCO}\n")
    
    if not os.path.exists(DIRETORIO_BANCO):
        print(f"❌ Erro: A pasta '{DIRETORIO_BANCO}' não foi encontrada.")
        print("   Rode o script de geração (gerar_tudo_final.py) primeiro.")
        return

    palavras_encontradas = 0
    total_arquivos = 0
    
    # Pega todas as pastas e ordena alfabeticamente para facilitar a leitura
    try:
        itens = sorted(os.listdir(DIRETORIO_BANCO))
    except Exception as e:
        print(f"❌ Erro ao ler diretório: {e}")
        return
    
    for item in itens:
        caminho_completo = os.path.join(DIRETORIO_BANCO, item)
        
        # Verifica se é uma pasta (cada pasta representa uma "Palavra-Chave")
        if os.path.isdir(caminho_completo):
            palavras_encontradas += 1
            
            # Lista as temperaturas (arquivos .mp3)
            arquivos = sorted([f for f in os.listdir(caminho_completo) if f.endswith(".mp3")])
            qtd = len(arquivos)
            total_arquivos += qtd
            
            # --- CABEÇALHO DA PALAVRA ---
            # Mostra a palavra e quantas variações ela tem
            status_cor = "✅" if qtd >= 3 else "⚠️" # Alerta se tiver poucas variações
            print(f"🔹 {item.upper()}  [{qtd} temps] {status_cor}") 
            
            if not arquivos:
                print("   ❌ [Vazio! Rode o gerador novamente]")
            
            for i, arq in enumerate(arquivos):
                temperatura = arq.replace(".mp3", "")
                
                # Desenha a árvore (└─ para o último, ├─ para os outros)
                conector = "└─" if i == len(arquivos) - 1 else "├─"
                
                # Formatação visual: Palavra > Temperatura
                print(f"   {conector} 🌡️  {temperatura}")
            
            # Espaço entre blocos
            print("") 

    print("=" * 50)
    print(f"📈 RESUMO ESTATÍSTICO:")
    print(f"   - Vocabulário Total: {palavras_encontradas} palavras")
    print(f"   - Banco de Voz:      {total_arquivos} arquivos de áudio")
    print("=" * 50)

if __name__ == "__main__":
    listar_estoque()