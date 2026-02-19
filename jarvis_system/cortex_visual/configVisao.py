import os

# --- HARDWARE ---
# ID da Câmera (0 é a padrão, 1 seria uma externa USB)
CAMERA_ID = 0

# Taxa de Quadros Alvo (Isso ajuda a não fritar a CPU tentando pegar 60fps)
TARGET_FPS = 30

# Resolução de Captura 
# 640x480 é o ideal para CPU. Se tiveres GPU configurada, podes tentar 1280x720.
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# --- INTELIGÊNCIA ARTIFICIAL ---
# Intervalo de Verificação (IMPORTANTE)
# 3.0s é muito lento para interação humana (parece que ele trava).
# 0.5s é o equilíbrio perfeito: o sistema reage rápido, mas deixa o áudio respirar.
FACE_CHECK_INTERVAL = 0.5 

# Tolerância de Identificação
# 0.6 = Padrão (pode confundir pessoas parecidas)
# 0.5 = Rigoroso (melhor segurança)
# 0.4 = Muito Rigoroso (pode não te reconhecer se a luz mudar)
TOLERANCE = 0.55

# Modelo de Detecção
# 'hog' = Mais rápido, roda bem em CPU (RECOMENDADO AGORA)
# 'cnn' = Muito preciso, mas exige placa NVIDIA com CUDA (Dlib compilado)
DETECTION_MODEL = "hog"

# --- INTERFACE VISUAL (HUD) ---
# Cores no formato BGR (Blue, Green, Red) - Padrão do OpenCV
COLOR_KNOWN = (0, 255, 0)      # Verde Neon
COLOR_UNKNOWN = (0, 0, 255)    # Vermelho Alerta
COLOR_UI = (255, 255, 0)       # Ciano/Amarelo para textos
FONT_SCALE = 0.6
THICKNESS = 2

# --- SISTEMA DE ARQUIVOS (ROBUSTEZ) ---
# Calcula o caminho absoluto para evitar erros de "File not found"
current_dir = os.path.dirname(os.path.abspath(__file__))

# Estrutura: jarvis_system/cortex_visual/../data/visual_memory
# Resulta em: jarvis_system/data/visual_memory
base_data_path = os.path.abspath(os.path.join(current_dir, "..", "data"))
MEMORY_PATH = os.path.join(base_data_path, "visual_memory")

# 🔥 MELHORIA: Cria a pasta automaticamente se ela não existir
# Isso evita que o sistema crashe no primeiro boot
if not os.path.exists(MEMORY_PATH):
    try:
        os.makedirs(MEMORY_PATH)
        print(f"[CONFIG] Pasta de memória criada: {MEMORY_PATH}")
    except Exception as e:
        print(f"[CONFIG] Erro crítico ao criar pasta de memória: {e}")