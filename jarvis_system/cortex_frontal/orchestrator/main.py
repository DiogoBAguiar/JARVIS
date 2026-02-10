# jarvis_system/cortex_frontal/orchestrator/main.py
import time
import re
import random
from typing import Optional

from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos

# Dependências
try:
    from jarvis_system.cortex_motor.tool_registry import registry
    from jarvis_system.cortex_motor.launcher import launcher 
    from jarvis_system.cortex_frontal.brain_llm import llm 
    from jarvis_system.cortex_frontal.curiosity import curiosity
    from jarvis_system.hipocampo.reflexos import reflexos
except ImportError:
    registry, launcher, llm, curiosity, reflexos = None, None, None, None, None

# Módulos Locais
from .config import CONFIRMATION_YES, CONFIRMATION_NO
from .attention import AttentionSystem
from .learning import LearningHandler
from .tools_handler import ToolsHandler
from .cognition import CognitionHandler

class Orchestrator:
    def __init__(self):
        self.log = JarvisLogger("CORTEX_FRONTAL")
        
        # Subsistemas
        self.attention = AttentionSystem()
        self.learner = LearningHandler(reflexos)
        self.tools = ToolsHandler(launcher, registry)
        self.cognitive = CognitionHandler(llm, curiosity)
        
        self.pending_context: Optional[dict] = None
        
        # Barramento
        bus.inscrever(Eventos.FALA_RECONHECIDA, self.process_input)
        self.log.info("🧠 Córtex Frontal (Modular v4.0) Online.")

    def process_input(self, evento: Evento):
        raw_text = evento.dados.get("texto", "")
        if not raw_text: return

        # 1. Normalização Básica
        clean_text = re.sub(r'[^\w\s]', '', raw_text.lower()).strip()
        clean_text = re.sub(r'(.)\1{2,}', r'\1', clean_text) # Remove letras repetidas (oooi)

        # 2. Confirmações Pendentes (Prioridade Máxima)
        if self._handle_confirmation(clean_text): return

        # 3. Atenção (Wake Word)
        is_active, payload = self.attention.check(clean_text)
        if not is_active: return

        if not payload:
            self._speak(random.choice(["Pois não?", "Estou aqui.", "Sim?", "Às ordens."]))
            return

        self.log.info(f"🤔 Processando: '{payload}'")

        # 4. Pipeline de Execução
        try:
            # 4.1 Aprendizado Rápido ("Aprenda que X é Y")
            ok, msg = self.learner.handle(payload)
            if ok:
                self._speak(msg)
                return

            # 4.2 Comandos Diretos (Sem LLM - Mais rápido)
            ok, msg = self.tools.handle_direct_command(payload)
            if ok:
                self._speak(msg)
                return

            # 4.3 Cognição (LLM + JSON)
            response_text, json_action = self.cognitive.process(payload)
            
            if json_action:
                self._execute_json_action(json_action)
            elif response_text:
                self._speak(response_text)

        except Exception as e:
            self.log.error(f"Erro no pipeline: {e}")
            self._speak("(serious) Ocorreu um erro interno no processamento.")

    def _handle_confirmation(self, text: str) -> bool:
        if not self.pending_context: return False
        
        words = text.split()
        if any(w in words for w in CONFIRMATION_YES):
            self._execute_pending()
            return True
        elif any(w in words for w in CONFIRMATION_NO):
            self._speak("Cancelado.")
            self.pending_context = None
            return True
        return False

    def _execute_pending(self):
        ctx = self.pending_context
        if ctx["type"] == "app_suggestion":
            self._speak(f"Abrindo {ctx['name']}.")
            if launcher: launcher.abrir_por_caminho(ctx["path"])
            # Aprende para a próxima vez
            if reflexos: 
                reflexos.adicionar_correcao(ctx["original_term"], ctx["name"].lower())
        
        self.pending_context = None

    def _execute_json_action(self, action: dict):
        tool = action.get("ferramenta")
        
        if tool == "memoria_gravar":
            dado = action.get("dado") or action.get("parametro")
            if llm: llm.ensinar(dado)
            self._speak(f"Memorizado: {dado}")
            return

        if tool in ["spotify", "sistema"]:
            cmd = action.get("comando")
            msg = self.tools.execute_tool_from_llm(tool, cmd)
            self._speak(msg)
            return

    def _speak(self, text: str):
        bus.publicar(Evento(Eventos.FALAR, {"texto": text}))

    def start(self): pass
    def stop(self): pass