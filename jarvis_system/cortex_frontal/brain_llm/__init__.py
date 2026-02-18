# jarvis_system/cortex_frontal/brain_llm/__init__.py
import logging
from .hybridBrain import HybridBrain

log = logging.getLogger("BRAIN_INIT")
llm = None

try:
    # Instancia o Singleton
    llm = HybridBrain()
except Exception as e:
    log.critical(f"❌ Falha Fatal ao iniciar Córtex Frontal: {e}")