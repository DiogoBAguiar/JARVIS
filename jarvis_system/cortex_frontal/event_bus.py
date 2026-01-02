from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from jarvis_system.cortex_frontal.observability import JarvisLogger

# Inicializa o logger específico para o barramento
log = JarvisLogger("EVENT_BUS")

@dataclass
class Evento:
    """Estrutura padrão de uma mensagem no sistema nervoso do Jarvis."""
    nome: str
    dados: Dict[str, Any]

class EventBus:
    """
    Barramento de Eventos Central (Pub/Sub).
    Desacopla produtores (ex: microfone) de consumidores (ex: orquestrador).
    """
    def __init__(self):
        # Dicionário mapeando Nome do Evento -> Lista de Funções Callback
        self._assinantes: Dict[str, List[Callable]] = {}

    def inscrever(self, evento_nome: str, callback: Callable):
        """Registra uma função para ser chamada quando um evento ocorrer."""
        if evento_nome not in self._assinantes:
            self._assinantes[evento_nome] = []
        
        self._assinantes[evento_nome].append(callback)
        log.debug(f"Novo assinante registrado para: {evento_nome}")

    def publicar(self, evento: Evento):
        """Distribui o evento para todos os interessados."""
        if evento.nome in self._assinantes:
            for callback in self._assinantes[evento.nome]:
                try:
                    # Execução protegida para que um erro num ouvinte não quebre o bus
                    callback(evento)
                except Exception as e:
                    log.error(
                        f"Erro ao processar evento '{evento.nome}'", 
                        error=str(e),
                        subscriber=getattr(callback, "__name__", "unknown")
                    )
        else:
            log.warning(f"Evento publicado sem assinantes: {evento.nome}")

# Instância Singleton Global (padrão de projeto para acesso único)
bus = EventBus()