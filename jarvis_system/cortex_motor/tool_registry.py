from typing import Callable, Dict, Any, Optional
from dataclasses import dataclass
from jarvis_system.cortex_frontal.observability import JarvisLogger

# --- IMPORTAÇÃO DOS AGENTES ESPECIALISTAS (LEVES) ---
# Mantemos no topo apenas os agentes que NÃO usam bibliotecas pesadas (como ChromaDB/Torch)
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

# OBS: O AgenteSpotify foi removido daqui para evitar Deadlock no Windows
# Ele será importado sob demanda dentro da classe ToolRegistry.

# Padronização do nome do logger
log = JarvisLogger("MOTOR_REGISTRY")

@dataclass
class ToolDefinition:
    """Metadados de uma ferramenta funcional simples."""
    name: str
    description: str
    func: Callable
    safe_mode: bool = True 

class ToolRegistry:
    """
    Gerenciador central de capacidades do Jarvis.
    Singleton Registry - Suporta Funções e Agentes Especialistas.
    """
    def __init__(self):
        # Armazena ferramentas simples (funções decoradas)
        self._tools: Dict[str, ToolDefinition] = {}
        # Armazena agentes complexos (classes especialistas)
        self._agentes: Dict[str, Any] = {}
        
        # Inicializa os especialistas automaticamente
        self._carregar_especialistas()

    def _carregar_especialistas(self):
        """Instancia e registra os agentes especialistas disponíveis."""
        
        # 1. Lista de Agentes Leves (Importados no topo)
        lista_classes = [
            AgenteCalendario,
            AgenteSistema,
            AgenteClima,
            AgenteMedia,
        ]

        # 2. IMPORTAÇÃO TARDIA (LAZY IMPORT) DO SPOTIFY
        # Resolve o erro de "Import Lock Deadlock" no Windows com multiprocessing.
        # Só importamos o módulo pesado quando esta função é executada pelo processo pai.
        try:
            from jarvis_system.agentes_especialistas.spotify.agent import AgenteSpotify
            lista_classes.append(AgenteSpotify)
            # log.debug("🔧 Módulo Spotify importado com sucesso (Lazy Load).")
        except ImportError:
            log.warning("⚠️ Agente Spotify não encontrado ou dependências ausentes.")
        except Exception as e:
            log.error(f"❌ Erro ao importar Agente Spotify: {e}")

        # 3. Instanciação e Registro
        for ClasseAgente in lista_classes:
            if ClasseAgente:
                try:
                    agente = ClasseAgente()
                    self._agentes[agente.nome] = agente
                    log.info(f"🎓 Especialista Integrado: {agente.nome.upper()}")
                except Exception as e:
                    log.error(f"Falha ao carregar agente {ClasseAgente}: {e}")

    def register(self, name: str, description: str, safe_mode: bool = True):
        """
        Decorator para registrar funções simples como ferramentas.
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
            log.debug(f"🔧 Ferramenta funcional registrada: '{name}'")
            return func
        return decorator

    def list_tools(self) -> list[str]:
        """Lista todas as ferramentas e agentes disponíveis."""
        func_tools = list(self._tools.keys())
        agent_tools = list(self._agentes.keys())
        return func_tools + agent_tools

    def identificar_agente(self, texto: str) -> Optional[str]:
        """
        Tenta descobrir qual Agente Especialista deve tratar o texto
        baseado nos gatilhos (palavras-chave) definidos no agente.
        """
        texto_lower = texto.lower()
        for nome, agente in self._agentes.items():
            # Verifica se o agente tem a propriedade 'gatilhos'
            if hasattr(agente, 'gatilhos'):
                for gatilho in agente.gatilhos:
                    if gatilho in texto_lower:
                        return nome
        return None

    def execute(self, tool_name: str, **kwargs) -> Any:
        """
        Executa uma ferramenta (seja função ou agente) blindada contra falhas.
        """
        # 1. Verifica se é um Agente Especialista
        if tool_name in self._agentes:
            agente = self._agentes[tool_name]
            try:
                log.info(f"🎩 Delegando para Especialista: {tool_name}")
                # O comando principal geralmente vem no kwargs ou como primeiro argumento
                # Adaptação para garantir que o texto chegue ao agente
                comando = kwargs.get('comando') or kwargs.get('texto') or ""
                return agente.executar(comando)
            except Exception as e:
                log.error(f"❌ Falha no Agente {tool_name}: {e}")
                return f"O especialista {tool_name} encontrou um erro."

        # 2. Verifica se é uma Ferramenta Funcional
        if tool_name in self._tools:
            tool = self._tools[tool_name]
            try:
                log.info(f"🚀 Executando Tool: {tool_name} {kwargs if kwargs else ''}")
                return tool.func(**kwargs)
            except Exception as e:
                log.error(f"❌ Falha crítica na ferramenta {tool_name}: {e}")
                return f"Falha ao executar {tool_name}."

        # 3. Não encontrou nada
        log.error(f"Tentativa de execução de ferramenta fantasma: {tool_name}")
        return f"Erro: A ferramenta ou agente '{tool_name}' não está registrado."

# Instância global
registry = ToolRegistry()