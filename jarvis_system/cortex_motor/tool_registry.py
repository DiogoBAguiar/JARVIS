import json
import importlib
import pkgutil
import inspect
from typing import Callable, Dict, Any, Optional, Type
from dataclasses import dataclass
from pydantic import BaseModel, ValidationError

from jarvis_system.cortex_frontal.observability import JarvisLogger

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
    """
    Coração da Extensibilidade do Orquestrador.
    Utiliza Auto-Discovery para carregar Agentes dinamicamente.
    """
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._agentes: Dict[str, Any] = {}
        
        # Dicionário fixo de descrições para guiar o LLM corretamente e evitar "Fantasmas"
        self._descricoes_agentes = {
            "sistema": "Controla hardware (bateria, brilho, volume, memoria, cpu) e ABRE APLICATIVOS LOCAIS/SITES. REGRA ESTRITA: Se o usuário pedir para abrir, executar, iniciar QUALQUER programa (incluindo calculadora, bloco de notas, jogos, sites), você DEVE usar a ferramenta 'sistema'. NUNCA invente uma ferramenta chamada 'calculadora'.",
            "clima": "Fornece informações meteorológicas atuais e previsões do tempo.",
            "calendario": "Gerencia eventos, lembretes, datas e alarmes do calendário.",
            "media": "Controla mídia local geral (Pausar, dar Play em players de vídeo/áudio).",
            "spotify": "Toca músicas, playlists, álbuns e artistas especificamente no Spotify. Passe o nome da música e o artista no parâmetro 'comando'."
        }
        
        self._carregar_especialistas_dinamicamente()

    def _carregar_especialistas_dinamicamente(self):
        """Varre o pacote 'agentes_especialistas' e carrega automaticamente."""
        try:
            import jarvis_system.agentes_especialistas as pacote_agentes
            from jarvis_system.agentes_especialistas.base_agente import AgenteEspecialista
        except ImportError as e:
            log.critical(f"❌ Falha crítica ao acessar o pacote base de agentes: {e}")
            return

        prefixo_pacote = pacote_agentes.__name__ + "."

        for _, nome_modulo, _ in pkgutil.walk_packages(pacote_agentes.__path__, prefixo_pacote):
            try:
                modulo = importlib.import_module(nome_modulo)
                for _, classe_encontrada in inspect.getmembers(modulo, inspect.isclass):
                    if issubclass(classe_encontrada, AgenteEspecialista) and classe_encontrada is not AgenteEspecialista:
                        if classe_encontrada.__module__ == nome_modulo:
                            try:
                                agente = classe_encontrada()
                                if agente.nome not in self._agentes:
                                    self._agentes[agente.nome] = agente
                                    log.info(f"🎓 Especialista Integrado (Auto-Discovery): {agente.nome.upper()}")
                            except Exception as erro_instancia:
                                log.error(f"❌ Falha ao instanciar o agente '{classe_encontrada.__name__}': {erro_instancia}")
                                
            except ImportError as erro_importacao:
                log.debug(f"⚠️ Ignorando módulo '{nome_modulo}' (Dependências ausentes): {erro_importacao}")
            except Exception as erro_geral:
                log.debug(f"Ignorando módulo '{nome_modulo}' na varredura: {erro_geral}")

    # MÉTODOS DE INTERFACE EM INGLÊS (MANTIDOS PARA COMPATIBILIDADE COM ORQUESTRADOR)
    
    def register(self, name: str, description: str, schema: Type[BaseModel] = None, safe_mode: bool = True):
        def decorador(funcao: Callable):
            if name in self._tools:
                log.warning(f"⚠️ Sobrescrevendo ferramenta funcional: {name}")
            
            self._tools[name] = ToolDefinition(
                name=name, description=description, func=funcao,
                parameters_schema=schema, safe_mode=safe_mode
            )
            log.debug(f"🔧 Ferramenta funcional registrada: '{name}'")
            return funcao
        return decorador

    def list_tools(self) -> list[str]:
        return list(self._tools.keys()) + list(self._agentes.keys())

    def get_all_tool_descriptions(self) -> str:
        descricoes = []
        for nome, agente in self._agentes.items():
            descricao_texto = self._descricoes_agentes.get(nome, getattr(agente, 'descricao', f"Agente especialista em {nome}"))
            descricoes.append(f"- Ferramenta: '{nome}' | Uso: {descricao_texto}")
            
        for nome, ferramenta in self._tools.items():
            descricoes.append(f"- Ferramenta: '{nome}' | Uso: {ferramenta.description}")
            
        return "\n".join(descricoes)

    def execute(self, tool_name: str, **kwargs) -> Any:
        # =========================================================
        # 🛡️ INTERCEPTADOR DE ALUCINAÇÕES (O "Filtro de Teimosia")
        # =========================================================
        # Se o LLM inventar estas ferramentas, nós roteamos à força para o agente correto
        alucinacoes_de_sistema = [
            "calculadora", "league_of_legends", "bloco_de_notas", "notepad",
            "navegador", "browser", "youtube", "google", "whatsapp"
        ]
        
        if tool_name in alucinacoes_de_sistema:
            log.warning(f"🛡️ Interceptando fantasma '{tool_name}' -> Roteando para 'sistema'")
            # Reempacota os argumentos para o Agente Sistema entender
            comando_original = kwargs.get('comando', '')
            expressao = kwargs.get('expressao', '')
            kwargs['comando'] = f"abrir {tool_name} {comando_original} {expressao}".strip()
            tool_name = "sistema"

        # =========================================================
        # DELEGAÇÃO PARA AGENTES
        # =========================================================
        if tool_name in self._agentes:
            agente = self._agentes[tool_name]
            try:
                log.info(f"🎩 Delegando para Especialista: {tool_name}")
                
                comando_base = kwargs.pop('comando', None) or kwargs.pop('texto', None) or ""
                argumentos_extras = " ".join(str(valor) for valor in kwargs.values() if isinstance(valor, str))
                comando_final = f"{comando_base} {argumentos_extras}".strip()
                
                return agente.executar(comando_final, **kwargs)
                
            except Exception as e:
                log.error(f"❌ Falha no Agente {tool_name}: {e}")
                return f"O especialista {tool_name} encontrou um erro: {e}"

        # =========================================================
        # EXECUÇÃO DE TOOLS SIMPLES
        # =========================================================
        if tool_name in self._tools:
            ferramenta = self._tools[tool_name]
            try:
                log.info(f"🚀 Executando Tool: {tool_name}")
                if ferramenta.parameters_schema:
                    try:
                        argumentos_validados = ferramenta.parameters_schema.model_validate(kwargs)
                        kwargs_seguros = argumentos_validados.model_dump()
                    except ValidationError as erro_validacao:
                        mensagem_erro = f"Erro Sintático: {str(erro_validacao)}. Corrija o payload JSON."
                        log.warning(f"🛡️ Blindagem ativada: {mensagem_erro}")
                        return json.dumps({"status": "execution_failed", "error": mensagem_erro})
                else:
                    kwargs_seguros = kwargs

                resultado = ferramenta.func(**kwargs_seguros)
                return json.dumps({"status": "success", "data": resultado})

            except Exception as e:
                log.error(f"❌ Falha crítica na ferramenta {tool_name}: {e}")
                return json.dumps({"status": "execution_failed", "error": str(e)})

        # Se for um fantasma de conhecimento puro (ex: explicador), devolvemos os dados como texto normal
        if tool_name in ["conhecimento", "explicador", "pesquisa", "informacao", "chat"]:
            topico = kwargs.get('topico') or kwargs.get('assunto') or kwargs.get('comando') or ""
            return f"Pesquisa sobre {topico} processada mentalmente."

        log.error(f"Tentativa de execução de ferramenta fantasma: {tool_name}")
        return json.dumps({"status": "error", "message": f"Ferramenta '{tool_name}' não existe."})

registry = ToolRegistry()