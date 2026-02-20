# jarvis_system/cortex_frontal/orchestrator/orchestrator.py
import time
import re
import random
from typing import Optional

from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos

# Dependências Globais
try:
    from jarvis_system.cortex_motor.tool_registry import registry
    from jarvis_system.cortex_motor.appLauncher import launcher 
    from jarvis_system.cortex_frontal.brain_llm import llm 
    from jarvis_system.cortex_frontal.curiosityEngine import curiosity
    from jarvis_system.hipocampo.reflexos import reflexos
except ImportError:
    registry, launcher, llm, curiosity, reflexos = None, None, None, None, None

# Módulos Locais
from .configOrchestrator import CONFIRMATION_YES, CONFIRMATION_NO
from .attentionSystem import AttentionSystem
from .learningHandler import LearningHandler
from .toolsHandler import ToolsHandler
from .cognitionHandler import CognitionHandler

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
        self.log.info("🧠 Córtex Frontal (Modular v4.0) Instanciado.")

    # -------------------------------------------------------------------------
    # 🕵️‍♂️ VERIFICAÇÃO REAL DO ESTADO (A CORREÇÃO)
    # -------------------------------------------------------------------------
    @property
    def sistemas_carregados(self) -> bool:
        return True

    # -------------------------------------------------------------------------

    def process_input(self, evento: Evento):
        raw_text = evento.dados.get("texto", "")
        if not raw_text: return
        
        # 🚨 LOG DE DEBUG: Vamos ver se o Orquestrador pelo menos acorda!
        self.log.info(f"📥 Chegou no Orquestrador: '{raw_text}'")

        # Ignora comandos se o sistema ainda não estiver 100% carregado
        if not self.sistemas_carregados:
            self.log.warning("⚠️ Comando ignorado! A trava 'sistemas_carregados' está bloqueando (menos de 3 agentes no Registry).")
            return

        # 1. Normalização Básica
        clean_text = re.sub(r'[^\w\s]', '', raw_text.lower()).strip()
        clean_text = re.sub(r'(.)\1{2,}', r'\1', clean_text) 

        # 2. Confirmações Pendentes
        if self._handle_confirmation(clean_text): return

        # 3. Atenção (Wake Word)
        is_active, payload = self.attention.check(clean_text)
        
        if not is_active: 
            self.log.warning(f"⚠️ Comando ignorado! A palavra de ativação (Jarvis) não foi validada em: '{clean_text}'")
            return

        if not payload:
            self._speak(random.choice(["Pois não?", "Estou aqui.", "Sim?", "Às ordens."]))
            return

        self.log.info(f"🤔 Processando: '{payload}'")

        # 4. Pipeline de Execução
        try:
            # 4.1 Aprendizado Rápido
            ok, msg = self.learner.handle(payload)
            if ok:
                self._speak(msg)
                return

            # 4.2 Comandos Diretos
            ok, msg = self.tools.handle_direct_command(payload)
            if ok:
                self._speak(msg)
                return

            # 4.3 Cognição (LLM)
            response_text, json_action = self.cognitive.process(payload)
            
            if json_action:
                self._execute_json_action(json_action)
            elif response_text:
                self._speak(response_text)

        except Exception as e:
            self.log.error(f"Erro no pipeline: {e}")
            self._speak("Ocorreu um erro interno no processamento.")

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

    def start(self):
        # Apenas logamos. A propriedade 'sistemas_carregados' agora faz a verificação real
        # dinamicamente sempre que a API perguntar.
        self.log.info("🧠 Córtex Frontal iniciado (Aguardando especialistas...).")

    def stop(self):
        pass