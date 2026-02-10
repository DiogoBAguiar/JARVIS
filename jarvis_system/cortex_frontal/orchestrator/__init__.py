# jarvis_system/cortex_frontal/orchestrator/__init__.py
import logging
from .main import Orchestrator

log = logging.getLogger("ORCH_INIT")
maestro = None

try:
    maestro = Orchestrator()
except Exception as e:
    log.critical(f"❌ Falha Fatal no Orchestrator: {e}")