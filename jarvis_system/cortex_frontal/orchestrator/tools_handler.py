# jarvis_system/cortex_frontal/orchestrator/tools_handler.py
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos

log = JarvisLogger("ORCH_TOOLS")

class ToolsHandler:
    def __init__(self, launcher, registry):
        self.launcher = launcher
        self.registry = registry

    def handle_direct_command(self, text: str) -> tuple[bool, str]:
        """Tenta executar comandos diretos sem passar pelo LLM."""
        
        # 1. Sistema
        if "desligar sistema" in text or "desligar protocolos" in text:
            bus.publicar(Evento(Eventos.SHUTDOWN, {}))
            return True, "Desligando protocolos. Até logo."
            
        if text == "volume":
            if self.registry:
                self.registry.execute("sistema", comando="aumenta o volume")
            return True, "Painel de volume acionado."

        # 2. Launcher (Ex: "Abrir Chrome")
        verbs = ["abrir", "iniciar", "executar", "rodar"]
        for v in verbs:
            if text.startswith(v + " "):
                app_name = text[len(v):].strip()
                if self.launcher:
                    status, nome, path = self.launcher.buscar_candidato(app_name)
                    if status == "EXATO":
                        self.launcher.abrir_por_caminho(path)
                        return True, f"Abrindo {nome}."
                    # Se for sugestão, deixamos o Orchestrator lidar com confirmação (pendente)
        
        # 3. Música (Spotify)
        music_verbs = ["tocar", "toca", "ouvir", "bota", "play", "pausar", "proxima"]
        if any(text.startswith(v) for v in music_verbs):
            if self.registry:
                res = self.registry.execute("spotify", comando=text)
                return True, str(res)

        return False, ""

    def execute_tool_from_llm(self, tool_name: str, command: str) -> str:
        """Executa ferramenta solicitada via JSON do LLM."""
        
        if tool_name == "spotify":
            if self.registry:
                return str(self.registry.execute("spotify", comando=command))
        
        if tool_name == "sistema":
            # Reutiliza a lógica de launcher se o comando for "abrir x"
            if command.startswith("abrir"):
                ok, msg = self.handle_direct_command(command)
                if ok: return msg
            # Outros comandos de sistema podem ser implementados aqui
            
        return "Ferramenta não encontrada ou comando inválido."