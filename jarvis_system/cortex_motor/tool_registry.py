from typing import Callable, Dict, Any, Optional
from dataclasses import dataclass
from jarvis_system.cortex_frontal.observability import JarvisLogger

# Inicializa logger específico para o Cortex Motor
log = JarvisLogger(__name__)

@dataclass
class ToolDefinition:
    """Metadados de uma ferramenta registrada."""
    name: str
    description: str
    func: Callable
    safe_mode: bool = True  # Se True, não exige aprovação humana (futuro)

class ToolRegistry:
    """
    Gerenciador central de capacidades do Jarvis.
    Padrão: Singleton Registry.
    """
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, name: str, description: str, safe_mode: bool = True):
        """
        Decorator para registrar funções como ferramentas do Jarvis.
        """
        def decorator(func: Callable):
            if name in self._tools:
                log.warning(f"Sobrescrevendo ferramenta existente: {name}")
            
            self._tools[name] = ToolDefinition(
                name=name,
                description=description,
                func=func,
                safe_mode=safe_mode
            )
            log.debug(f"Ferramenta registrada: '{name}'")
            return func
        return decorator

    def list_tools(self) -> list[str]:
        """Retorna lista de nomes de ferramentas disponíveis."""
        return list(self._tools.keys())

    def execute(self, tool_name: str, **kwargs) -> Any:
        """
        Executa uma ferramenta de forma controlada e auditada.
        """
        if tool_name not in self._tools:
            log.error(f"Tentativa de execução de ferramenta inexistente: {tool_name}")
            raise ValueError(f"Ferramenta '{tool_name}' não encontrada no registro.")

        tool = self._tools[tool_name]
        
        try:
            log.info(f"Iniciando execução: {tool_name}", params=kwargs)
            # Aqui, no futuro, entraremos com validação de tipos via Pydantic
            result = tool.func(**kwargs)
            log.info(f"Execução finalizada: {tool_name}")
            return result
        
        except Exception as e:
            # Captura a falha, loga o contexto e re-lança para o Orchestrator decidir
            log.error(f"Falha crítica na ferramenta {tool_name}", error=str(e))
            raise e

# Instância global do registro
registry = ToolRegistry()