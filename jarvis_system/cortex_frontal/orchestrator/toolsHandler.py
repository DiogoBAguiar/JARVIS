# jarvis_system/cortex_frontal/orchestrator/toolsHandler.py
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos
import re

log = JarvisLogger("ORCH_TOOLS")

class ToolsHandler:
    def __init__(self, launcher, registry):
        self.launcher = launcher
        self.registry = registry

    def handle_direct_command(self, text: str) -> tuple[bool, str]:
        """Tenta executar comandos diretos sem passar pelo LLM."""
        
        # 1. Blindagem crítica: Previne o erro "cannot unpack non-iterable NoneType"
        # que quebra o pipeline do orquestrador se o input chegar vazio/nulo.
        if not text:
            return False, ""
        
        # 2. Sistema
        if "desligar sistema" in text or "desligar protocolos" in text:
            bus.publicar(Evento(Eventos.SHUTDOWN, {}))
            return True, "Desligando protocolos. Até logo."
            
        if text == "volume":
            if self.registry:
                self.registry.execute("sistema", comando="aumenta o volume")
            return True, "Painel de volume acionado."

        # 3. Launcher (Ex: "Abrir Chrome")
        verbs = ["abrir", "iniciar", "executar", "rodar"]
        for v in verbs:
            if text.startswith(v + " "):
                app_name = text[len(v):].strip()
                if self.launcher:
                    status, nome, path = self.launcher.buscar_candidato(app_name)
                    if status == "EXATO":
                        self.launcher.abrir_por_caminho(path)
                        return True, f"Abrindo {nome}."
        
        # 4. Música (Spotify)
        if re.search(r"\b(toca|tocar|ouvir|bota|play|pausar|proxima|parar)\b", text):
            # Avisa que já entendeu a ordem
            bus.publicar(Evento(Eventos.FALAR, {"texto": "Um momento, senhor."}))
            
            try:
                # Chama o Agente Diretamente (Mantendo seu workaround para evitar Deadlocks no Windows)
                from jarvis_system.agentes_especialistas.spotify.agent.agenteSpotify import AgenteSpotify
                spotify_agent = AgenteSpotify()
                res = spotify_agent.executar(text)
                
                return True, str(res)
            except Exception as e:
                log.error(f"Erro ao tentar abrir o Spotify: {e}")
                return True, "Senhor, o Agente Especialista do Spotify reportou uma falha."
                
        return False, ""

    def execute_tool_from_llm(self, tool_name: str, **kwargs) -> str:
        """
        Executa ferramenta solicitada via JSON do LLM.
        Agora é dinâmico: ele apenas confia no Registry blindado (Fase 1).
        Não importa se você tem 2 ou 500 ferramentas, o código aqui não muda mais.
        """
        if not self.registry:
            log.error("Registry não está inicializado no ToolsHandler.")
            return "Erro interno: ToolRegistry inativo."
            
        log.info(f"Recebido do LLM -> Roteando para: '{tool_name}' com args: {kwargs}")
        
        # O Registry (que agora usa Pydantic) cuida de executar, validar falhas e retornar o JSON.
        return str(self.registry.execute(tool_name, **kwargs))