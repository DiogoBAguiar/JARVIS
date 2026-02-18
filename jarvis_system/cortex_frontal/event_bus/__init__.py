# jarvis_system/cortex_frontal/event_bus/__init__.py
import logging
from .model import Evento
from .eventBus import EventBus

# Logger de inicialização (fallback se o core falhar)
log = logging.getLogger("BUS_INIT")
bus = None

try:
    # Instância Singleton Global
    bus = EventBus()
except Exception as e:
    log.critical(f"❌ Falha Fatal ao criar EventBus: {e}")