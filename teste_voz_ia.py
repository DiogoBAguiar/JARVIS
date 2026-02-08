import time
import os
import pygame
from jarvis_system.cortex_frontal.voice_director import VoiceDirector

# Simulação do Banco de Dados de Frases que você já gerou
# (Aqui ele tenta achar o arquivo gerado anteriormente)
CAMINHO_BANCO_VOZ = "jarvis_system/area_broca/voice_bank_fish/frases_pro"

FRASES_TESTE = [
    "Senhor, todos os sistemas estão operacionais.",
    "Atenção! Detectei uma intrusão na rede.",
    "Claro, vamos fingir que essa foi uma boa ideia.",
    "O sistema observa e aprende.",
    "Desculpe, não encontrei esse arquivo.",
    "Bem-vindo de volta, senhor."
]

def tocar_audio(caminho):
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(caminho)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
    except Exception as e:
        print(f"   [Erro no Player]: {e}")

def main():
    diretor = VoiceDirector()
    
    print("🎙️ INICIANDO TESTE DE DIREÇÃO DE VOZ POR I.A.")
    print("="*60)

    for frase in FRASES_TESTE:
        print(f"\n📝 Frase: '{frase}'")
        
        # 1. A I.A. Decide a Emoção
        start = time.time()
        emocao_escolhida = diretor.analisar_tom(frase)
        tempo = time.time() - start
        
        print(f"🤖 I.A. Decidiu: [{emocao_escolhida.upper()}] ({tempo:.2f}s)")
        
        # 2. Mapeamento para categoria (Você precisa ajustar isso conforme suas pastas reais)
        # O script de geração salvou em pastas por CATEGORIA (cat), não por emoção.
        # Aqui tentamos adivinhar ou buscar no sistema de arquivos.
        
        # Busca "bruta" no sistema de arquivos pelo nome aproximado
        arquivo_encontrado = None
        nome_limpo = frase.lower().replace("jarvis", "j.a.r.v.i.s.").replace(" ", "_")[:20] # Pega o começo
        
        # Varre as pastas para tentar achar o arquivo
        if os.path.exists(CAMINHO_BANCO_VOZ):
            for root, dirs, files in os.walk(CAMINHO_BANCO_VOZ):
                for file in files:
                    # Verifica se o arquivo parece com a frase E se está na pasta da emoção certa (opcional)
                    # No seu script anterior, as pastas eram categorias (alerta, humor), não emoções.
                    # Mas podemos simular o 'match'.
                    
                    if nome_limpo in file: 
                        arquivo_encontrado = os.path.join(root, file)
                        break
                if arquivo_encontrado: break
        
        # 3. Resultado
        if arquivo_encontrado:
            print(f"✅ Arquivo Encontrado: {arquivo_encontrado}")
            print("🔊 Tocando...")
            tocar_audio(arquivo_encontrado)
        else:
            print(f"⚠️ Arquivo pré-gravado não encontrado.")
            print(f"   -> Sugestão: Gerar no Fish Audio com tag: ({emocao_escolhida}) {frase}")

if __name__ == "__main__":
    main()