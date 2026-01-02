from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from jarvis_system.cortex_frontal.observability import JarvisLogger

log = JarvisLogger("EVENT_BUS")

@dataclass
class Evento:
    nome: str
    dados: Dict[str, Any]

class EventBus:
    """
    Barramento de Eventos Central (Pub/Sub).
    Desacopla produtores (Ouvidos) de consumidores (Cérebro).
    """
    def __init__(self):
        self._assinantes: Dict[str, List[Callable]] = {}

    def inscrever(self, evento_nome: str, callback: Callable):
        if evento_nome not in self._assinantes:
            self._assinantes[evento_nome] = []
        self._assinantes[evento_nome].append(callback)
        log.debug(f"Novo assinante para: {evento_nome}")

    def publicar(self, evento: Evento):
        if evento.nome in self._assinantes:
            # Em sistemas reais, isso seria assíncrono (asyncio.create_task)
            # Para o MVP, síncrono é mais seguro e fácil de depurar.
            for callback in self._assinantes[evento.nome]:
                try:
                    callback(evento)
                except Exception as e:
                    log.error(f"Erro no processamento do evento {evento.nome}", error=str(e))
        else:
            log.warning(f"Evento sem assinantes: {evento.nome}")

# Singleton Global
bus = EventBus()