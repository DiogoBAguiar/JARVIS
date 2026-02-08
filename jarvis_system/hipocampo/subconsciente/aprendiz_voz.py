import os
import time
from jarvis_system.area_broca.fabrica_local import FabricaLocal

ARQUIVO_PENDENTE = os.path.join("jarvis_system", "data", "vocabulario_pendente.txt")

def processar_aprendizado_noturno():
    if not os.path.exists(ARQUIVO_PENDENTE):
        print("💤 Nada novo para aprender hoje.")
        return

    # Lê o que faltou durante o dia
    with open(ARQUIVO_PENDENTE, "r", encoding="utf-8") as f:
        palavras = [line.strip() for line in f.readlines() if line.strip()]

    if not palavras: return

    print(f"🧠 Subconsciente: Iniciando aprendizado de {len(palavras)} novas expressões...")
    
    # Inicializa a Fábrica Local (F5-TTS)
    fabrica = FabricaLocal()

    for palavra in palavras:
        # Gera as variações automaticamente
        fabrica.gerar_palavra(palavra, "neutro")
        fabrica.gerar_palavra(palavra, "urgente")
        fabrica.gerar_palavra(palavra, "duvida")
    
    # Limpa a lista de pendências
    open(ARQUIVO_PENDENTE, "w").close()
    print("✨ Vocabulário expandido com sucesso.")

if __name__ == "__main__":
    processar_aprendizado_noturno()