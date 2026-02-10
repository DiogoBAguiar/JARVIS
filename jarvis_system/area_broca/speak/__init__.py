# jarvis_system/area_broca/speak/__init__.py
from .main import NeuralSpeaker

# Instância Singleton Global (para manter compatibilidade com código antigo)
mouth = NeuralSpeaker()