import os
import asyncio
import edge_tts

# --- CONFIGURAÇÕES ---
OUTPUT_DIR = os.path.join(os.getcwd(), "jarvis_system", "area_broca", "voice_bank")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Vozes Brasileiras Disponíveis (Escolha a sua preferida):
# "pt-BR-AntonioNeural"   (Masculina, séria - Ótima para Jarvis)
# "pt-BR-FranciscaNeural" (Feminina, aguda)
# "pt-BR-ThalitaNeural"   (Feminina, jovem)
VOZ_JARVIS = "pt-BR-AntonioNeural"

class FabricaLocal:
    def __init__(self):
        print("\n🏭 Inicializando Motor Edge-TTS (Microsoft Azure)...")
        print(f"🎙️ Voz selecionada: {VOZ_JARVIS}")

    async def _gerar_audio_async(self, texto, arquivo_saida):
        # Aumentamos a velocidade (+10%) para ficar mais dinâmico
        communicate = edge_tts.Communicate(texto, VOZ_JARVIS, rate="+10%")
        await communicate.save(arquivo_saida)

    def gerar_palavra(self, nome_arquivo, texto_real, emocao="neutro"):
        pasta = os.path.join(OUTPUT_DIR, nome_arquivo.lower().replace(" ", "_"))
        os.makedirs(pasta, exist_ok=True)
        arquivo_final = os.path.join(pasta, f"{emocao}.wav")

        if os.path.exists(arquivo_final):
            print(f"⏩ Pulando '{nome_arquivo}' (já existe)")
            return

        print(f"🎙️ Gerando: '{texto_real}' ({emocao})...")
        
        # Ajuste simples de texto para emoção (Edge-TTS é muito expressivo)
        texto_final = texto_real
        if emocao == "urgente": texto_final = f"{texto_real}!"
        elif emocao == "duvida": texto_final = f"{texto_real}?"

        try:
            # O Edge-TTS é assíncrono, precisamos rodar assim:
            asyncio.run(self._gerar_audio_async(texto_final, arquivo_final))
            print(f"   💾 Salvo: {arquivo_final}")
        except Exception as e:
            print(f"   ❌ Erro: {e}")

# --- LISTA DE FALAS DO JARVIS ---
PALAVRAS_DO_SISTEMA = {
    "senhor": "Senhor.",
    "jarvis": "Járvis ao seu dispor.",
    "sistemas": "Sistemas operacionais.",
    "online": "Online e pronto.",
    "acesso": "Acesso autorizado.",
    "negado": "Acesso negado.",
    "processando": "Processando dados.",
    "entendido": "Entendido.",
    "pois não": "Pois não?",
    "sim": "Sim.",
    "não": "Não.",
    "ativando": "Iniciando protocolos.",
    "desativando": "Encerrando sistemas.",
    "erro": "Detectei um erro.",
    "analisando": "Estou analisando."
}

if __name__ == "__main__":
    fabrica = FabricaLocal()
    
    # Gera tudo de uma vez (Super rápido)
    for chave, texto in PALAVRAS_DO_SISTEMA.items():
        fabrica.gerar_palavra(chave, texto, "neutro")