from typing import Callable, Dict, Any
from dataclasses import dataclass
from jarvis_system.cortex_frontal.observability import JarvisLogger

# Padronização do nome do logger
log = JarvisLogger("MOTOR_REGISTRY")

@dataclass
class ToolDefinition:
    """Metadados de uma ferramenta registrada."""
    name: str
    description: str
    func: Callable
    safe_mode: bool = True 

class ToolRegistry:
    """
    Gerenciador central de capacidades do Jarvis.
    Singleton Registry.
    """
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, name: str, description: str, safe_mode: bool = True):
        """
        Decorator para registrar funções como ferramentas.
        """
        def decorator(func: Callable):
            if name in self._tools:
                log.warning(f"⚠️ Sobrescrevendo ferramenta: {name}")
            
            self._tools[name] = ToolDefinition(
                name=name,
                description=description,
                func=func,
                safe_mode=safe_mode
            )
            # Log nível DEBUG para não poluir o startup
            log.debug(f"🔧 Ferramenta registrada: '{name}'")
            return func
        return decorator

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def execute(self, tool_name: str, **kwargs) -> Any:
        """
        Executa uma ferramenta blindada contra falhas.
        Retorna sempre uma string ou dado seguro, nunca explode exceção.
        """
        if tool_name not in self._tools:
            log.error(f"Tentativa de execução de ferramenta fantasma: {tool_name}")
            return f"Erro: A ferramenta '{tool_name}' não está registrada."

        tool = self._tools[tool_name]
        
        try:
            log.info(f"🚀 Executando: {tool_name} {kwargs if kwargs else ''}")
            result = tool.func(**kwargs)
            return result
        
        except Exception as e:
            # Captura a falha para que o Jarvis possa verbalizar o erro em vez de morrer
            log.error(f"❌ Falha crítica na ferramenta {tool_name}: {e}")
            return f"Falha ao executar {tool_name}."

# Instância global
registry = ToolRegistry()