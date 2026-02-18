# jarvis_system/area_broca/listen/config.py

# --- CONSTANTES DE ÁUDIO ---
SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 4000       # Buffer menor = mais responsivo
LIMIAR_SILENCIO = 0.010 # Limiar de disparo do VAD
BLOCOS_PAUSA_FIM = 6    # Blocos de silêncio para considerar fim da frase
GANHO_MIC = 5.0         # Multiplicador digital de volume