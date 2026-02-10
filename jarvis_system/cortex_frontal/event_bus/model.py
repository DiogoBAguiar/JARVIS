# jarvis_system/cortex_frontal/event_bus/model.py
from dataclasses import dataclass
from typing import Dict, Any, Callable

@dataclass
class Evento:
    """
    Estrutura imutável de uma mensagem no sistema nervoso.
    Ex: Evento(nome="fala_reconhecida", dados={"texto": "Olá"})
    """
    nome: str
    dados: Dict[str, Any]

# Definição de Tipo para o Callback (Melhora o Intellisense e Type Hinting)
SubscriberFunc = Callable[[Evento], None]