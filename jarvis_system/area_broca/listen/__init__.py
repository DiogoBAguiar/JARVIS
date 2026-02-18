# jarvis_system/area_broca/listen/__init__.py
import logging
from .ouvidoBiologico import OuvidoBiologico

logger = logging.getLogger("BROCA_INIT")
ears = None

try:
    logger.info("🔧 Instanciando singleton 'ears'...")
    ears = OuvidoBiologico(model_size="base", device="cpu")
except Exception as e:
    logger.error(f"❌ Erro ao instanciar OuvidoBiologico: {e}")