# jarvis_system/area_broca/speak/__init__.py
from .neuralSpeaker import NeuralSpeaker

# Instância Singleton Global (para manter compatibilidade com código antigo)
mouth = NeuralSpeaker()