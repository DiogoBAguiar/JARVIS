from typing import Dict, List, Callable, Any, Protocol
from dataclasses import dataclass
from jarvis_system.cortex_frontal.observability import JarvisLogger

# Inicializa o logger específico para o barramento
log = JarvisLogger("EVENT_BUS")

@dataclass
class Evento:
    """Estrutura imutável de uma mensagem no sistema nervoso."""
    nome: str
    dados: Dict[str, Any]

# Definição de Tipo para o Callback (Melhora o Intellisense)
SubscriberFunc = Callable[[Evento], None]

class EventBus:
    """
    Barramento de Eventos Central (Pub/Sub).
    Desacopla produtores (Listen) de consumidores (Brain/Speak).
    """
    def __init__(self):
        # Mapeia: NomeEvento -> Lista de Funções
        self._assinantes: Dict[str, List[SubscriberFunc]] = {}
        # Assinantes que ouvem TUDO (útil para logs e debug)
        self._wildcard_assinantes: List[SubscriberFunc] = []

    def inscrever(self, evento_nome: str, callback: SubscriberFunc):
        """
        Registra uma função para reagir a um evento específico.
        Use '*' como nome do evento para ouvir tudo.
        """
        if evento_nome == "*":
            self._wildcard_assinantes.append(callback)
            log.debug(f"Novo ouvinte GLOBAL registrado: {self._get_func_name(callback)}")
            return

        if evento_nome not in self._assinantes:
            self._assinantes[evento_nome] = []
        
        self._assinantes[evento_nome].append(callback)
        # Log verboso apenas para debug
        # log.debug(f"Novo assinante em '{evento_nome}': {self._get_func_name(callback)}")

    def publicar(self, evento: Evento):
        """
        Distribui o evento para todos os interessados (Síncrono).
        Atenção: Os callbacks devem ser rápidos ou rodar em thread separada.
        """
        # 1. Notifica ouvintes globais (Wildcards)
        for callback in self._wildcard_assinantes:
            self._safe_execute(callback, evento)

        # 2. Notifica ouvintes específicos
        if evento.nome in self._assinantes:
            for callback in self._assinantes[evento.nome]:
                self._safe_execute(callback, evento)
        elif not self._wildcard_assinantes:
            # Só avisa se ninguém (nem wildcards) ouviu
            log.warning(f"Evento órfão (sem ouvintes): {evento.nome}")

    def reset(self):
        """Limpa todos os assinantes (Útil para reinicialização do Kernel)."""
        self._assinantes.clear()
        self._wildcard_assinantes.clear()
        log.info("Barramento de eventos resetado.")

    def _safe_execute(self, callback: SubscriberFunc, evento: Evento):
        """Executa o callback protegendo o barramento contra quebras."""
        try:
            callback(evento)
        except Exception as e:
            nome_func = self._get_func_name(callback)
            log.error(f"Erro no assinante '{nome_func}' ao processar '{evento.nome}': {e}")

    def _get_func_name(self, func) -> str:
        """Helper para pegar o nome da função/método."""
        if hasattr(func, "__name__"):
            return func.__name__
        if hasattr(func, "func") and hasattr(func.func, "__name__"): # Partials
            return func.func.__name__
        return str(func)

# Instância Singleton Global
bus = EventBus()