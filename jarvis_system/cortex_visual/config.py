import os

# ID da Câmera (0 geralmente é a webcam integrada)
CAMERA_ID = 0

# Resolução de Captura (Menor = Mais Rápido)
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Intervalo de "Piscada" (Analisa biometria a cada X segundos para poupar CPU)
FACE_CHECK_INTERVAL = 3.0 

# Tolerância (0.6 é padrão, 0.5 é mais rigoroso/seguro)
TOLERANCE = 0.55

# --- CAMINHO DA MEMÓRIA VISUAL (CORRIGIDO) ---
# Sai de cortex_visual, volta para jarvis_system, entra em data
current_dir = os.path.dirname(os.path.abspath(__file__))
MEMORY_PATH = os.path.abspath(os.path.join(current_dir, "..", "data", "visual_memory"))