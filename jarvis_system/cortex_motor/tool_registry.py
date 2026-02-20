import json
from typing import Callable, Dict, Any, Optional, Type
from dataclasses import dataclass
from pydantic import BaseModel, ValidationError

from jarvis_system.cortex_frontal.observability import JarvisLogger

# --- IMPORTAÇÃO DOS AGENTES ESPECIALISTAS (LEVES) ---
try:
    from jarvis_system.agentes_especialistas.agente_calendario import AgenteCalendario
except ImportError:
    AgenteCalendario = None

try:
    from jarvis_system.agentes_especialistas.agente_sistema import AgenteSistema
except ImportError:
    AgenteSistema = None

try:
    from jarvis_system.agentes_especialistas.agente_clima import AgenteClima
except ImportError:
    AgenteClima = None

try:
    from jarvis_system.agentes_especialistas.agente_media import AgenteMedia
except ImportError:
    AgenteMedia = None

log = JarvisLogger("MOTOR_REGISTRY")

@dataclass
class ToolDefinition:
    """Metadados de uma ferramenta funcional simples, blindada."""
    name: str
    description: str
    func: Callable
    parameters_schema: Optional[Type[BaseModel]] = None
    safe_mode: bool = True 

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._agentes: Dict[str, Any] = {}
        self._carregar_especialistas()

    def _carregar_especialistas(self):
        lista_classes = [AgenteCalendario, AgenteSistema, AgenteClima, AgenteMedia]

        try:
            from jarvis_system.agentes_especialistas.spotify.agent import AgenteSpotify
            lista_classes.append(AgenteSpotify)
        except ImportError:
            log.warning("⚠️ Agente Spotify não encontrado ou dependências ausentes.")
        except Exception as e:
            log.error(f"❌ Erro ao importar Agente Spotify: {e}")

        for ClasseAgente in lista_classes:
            if ClasseAgente:
                try:
                    agente = ClasseAgente()
                    self._agentes[agente.nome] = agente
                    log.info(f"🎓 Especialista Integrado: {agente.nome.upper()}")
                except Exception as e:
                    log.error(f"Falha ao carregar agente {ClasseAgente}: {e}")

    def register(self, name: str, description: str, schema: Type[BaseModel] = None, safe_mode: bool = True):
        def decorator(func: Callable):
            if name in self._tools:
                log.warning(f"⚠️ Sobrescrevendo ferramenta: {name}")
            
            self._tools[name] = ToolDefinition(
                name=name, description=description, func=func,
                parameters_schema=schema, safe_mode=safe_mode
            )
            log.debug(f"🔧 Ferramenta funcional registrada: '{name}'")
            return func
        return decorator

    def list_tools(self) -> list[str]:
        return list(self._tools.keys()) + list(self._agentes.keys())

    def get_all_tool_descriptions(self) -> str:
        """
        FASE 3: Exporta o catálogo de ferramentas e agentes disponíveis.
        Será usado para injetar o contexto dinâmico no Prompt da IA.
        """
        desc = []
        for nome, agente in self._agentes.items():
            # Tenta pegar uma docstring ou atributo de descrição do agente
            descricao = getattr(agente, 'descricao', f"Agente especialista em {nome}")
            desc.append(f"- Ferramenta: '{nome}' | Uso: {descricao}")
            
        for nome, tool in self._tools.items():
            desc.append(f"- Ferramenta: '{nome}' | Uso: {tool.description}")
            
        return "\n".join(desc)

    def execute(self, tool_name: str, **kwargs) -> Any:
        if tool_name in self._agentes:
            agente = self._agentes[tool_name]
            try:
                log.info(f"🎩 Delegando para Especialista: {tool_name}")
                comando = kwargs.get('comando') or kwargs.get('texto') or ""
                return agente.executar(comando)
            except Exception as e:
                log.error(f"❌ Falha no Agente {tool_name}: {e}")
                return f"O especialista {tool_name} encontrou um erro."

        if tool_name in self._tools:
            tool = self._tools[tool_name]
            try:
                log.info(f"🚀 Executando Tool: {tool_name}")
                if tool.parameters_schema:
                    try:
                        validated_args = tool.parameters_schema.model_validate(kwargs)
                        safe_kwargs = validated_args.model_dump()
                    except ValidationError as validation_error:
                        error_msg = f"Erro Sintático: {str(validation_error)}. Corrija o payload JSON."
                        log.warning(f"🛡️ Blindagem ativada: {error_msg}")
                        return json.dumps({"status": "execution_failed", "error": error_msg})
                else:
                    safe_kwargs = kwargs

                resultado = tool.func(**safe_kwargs)
                return json.dumps({"status": "success", "data": resultado})

            except Exception as e:
                log.error(f"❌ Falha crítica na ferramenta {tool_name}: {e}")
                return json.dumps({"status": "execution_failed", "error": str(e)})

        log.error(f"Tentativa de execução de ferramenta fantasma: {tool_name}")
        return json.dumps({"status": "error", "message": f"Ferramenta '{tool_name}' não existe."})

registry = ToolRegistry()