# jarvis_system/area_broca/speak/config.py
import os
from dotenv import load_dotenv

load_dotenv()

FISH_AUDIO_API_URL = "https://api.fish.audio/v1/tts"
FISH_API_KEY = os.getenv("FISHAUDIO_API_KEY")
FISH_MODEL_ID = os.getenv("FISHAUDIO_MODEL_ID")

# --- MAPA DE EMOÇÕES (JARVIS -> FISH AUDIO) ---
FISH_TAGS = {
    # Contextos de Sistema
    "boot": "(confident)",
    "return": "(happy)",
    "query": "(curious)",
    "status": "(serious)",
    "passive": "(relaxed)",
    "alert": "(worried)",
    
    # Categorias Específicas
    "HUMOR": "(amused)",
    "COMBATE": "(shouting)",
    "FILOSOFIA": "(thoughtful)",
    "INTERACAO": "(helpful)",
    "STEALTH": "(whispering)",
    "DARK": "(serious)",
    
    # Adicione mais conforme necessário para alinhar com headme-contexto.md
}