import os
import sys

# Setup do path
sys.path.append(os.getcwd())

from jarvis_system.hipocampo.memoria import memoria
from jarvis_system.cortex_frontal.observability import JarvisLogger

log = JarvisLogger("MEMORY_CLEANER")

def limpar_tag():
    print("\n--- FAXINA DE MEMÓRIA ---")
    tag_alvo = input("Digite o nome da TAG para apagar (ex: playlist_Acadus): ").strip()
    
    if not tag_alvo:
        print("Operação cancelada.")
        return

    print(f"\n⚠️  ATENÇÃO: Você está prestes a apagar TODAS as memórias com a tag '{tag_alvo}'.")
    confirmacao = input("Tem certeza? Digite 'sim' para confirmar: ")
    
    if confirmacao.lower() == "sim":
        try:
            # Comando do ChromaDB para deletar baseada em metadados
            memoria.collection.delete(
                where={"tags": tag_alvo}
            )
            log.info(f"🗑️ Memórias com a tag '{tag_alvo}' foram deletadas com sucesso.")
            print("Pode rodar o scraper novamente agora.")
        except Exception as e:
            log.error(f"Erro ao limpar: {e}")
    else:
        print("Operação cancelada.")

if __name__ == "__main__":
    limpar_tag()