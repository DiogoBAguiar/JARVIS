import sys
import signal
import threading
import time
import os
from typing import List, Optional, Protocol
from dotenv import load_dotenv

# --- Configuração de Ambiente ---
load_dotenv()

# --- Interfaces (Contratos) ---
class Subsystem(Protocol):
    # O atributo 'name' é opcional no Protocol, mas útil se tiver
    def start(self) -> None: ...
    def stop(self) -> None: ...

# --- Imports do Core ---
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos

# --- IMPORTANTE: Importar a Classe do Orquestrador ---
from jarvis_system.cortex_frontal.orchestrator import Orchestrator

# --- Integração do Subconsciente (Aprendizado) ---
try:
    from jarvis_system.hipocampo.sonhar import dreamer
except ImportError:
    dreamer = None

# --- Kernel ---
class JarvisKernel:
    def __init__(self):
        self.log = JarvisLogger("KERNEL")
        self._shutdown_event = threading.Event()
        self._subsystems: List[Subsystem] = []

    def bootstrap(self):
        """Inicialização e Injeção de Dependências."""
        self.log.info("--- BOOTSTRAP: J.A.R.V.I.S. v2 ---")
        
        # 0. FASE DE SONHO (Aprendizado Offline)
        # Antes de acordar, processa as experiências (logs) passadas
        if dreamer:
            try:
                dreamer.processar_experiencias()
            except Exception as e:
                self.log.error(f"Falha no subsistema de sonhos: {e}")
        else:
            self.log.warning("Módulo 'sonhar' não encontrado. Aprendizado desativado.")

        self._check_environment()
        self._register_signal_handlers()
        self._setup_event_bus()
        
        # 1. Carrega Módulos Motores (Boca e Ouvido) via Factory Dinâmico
        self.mouth = self._load_module('jarvis_system.area_broca.speak', 'mouth')
        self.ears = self._load_module('jarvis_system.area_broca.listen', 'ears')
        
        # 2. Inicializa o CÉREBRO (Orquestrador)
        try:
            self.brain = Orchestrator()
            self._register_subsystem(self.brain)
            self.log.info("🧠 Córtex Frontal (Orquestrador) Acoplado.")
        except Exception as e:
            self.log.critical(f"❌ Falha ao iniciar Orquestrador: {e}")

        # 3. Registra os Sentidos
        if self.mouth: 
            # Adicionamos um atributo name dinamicamente para o log ficar bonito
            self.mouth.name = "Sistema de Fala" 
            self._register_subsystem(self.mouth)
            
        if self.ears: 
            self.ears.name = "Sistema Auditivo"
            self._register_subsystem(self.ears)

    def _check_environment(self):
        required = ["GROQ_API_KEY"]
        missing = [v for v in required if not os.getenv(v)]
        if missing:
            self.log.warning(f"⚠️ Variáveis ausentes: {missing}. O Cérebro Nuvem não funcionará.")

    def _load_module(self, path: str, attr_name: str) -> Optional[Subsystem]:
        try:
            module = __import__(path, fromlist=[attr_name])
            instance = getattr(module, attr_name)
            if instance is None:
                raise ImportError(f"Atributo {attr_name} é None")
            return instance
        except ImportError as e:
            self.log.warning(f"Subsistema não encontrado [{path}]: {e}")
            return None
        except Exception as e:
            self.log.error(f"Erro carregando [{path}]: {e}")
            return None

    def _register_subsystem(self, system: Subsystem):
        self._subsystems.append(system)
        name = getattr(system, 'name', system.__class__.__name__)
        self.log.debug(f"Subsistema registrado: {name}")

    def _register_signal_handlers(self):
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _setup_event_bus(self):
        bus.inscrever(Eventos.SHUTDOWN, self._handle_internal_shutdown)

    def _handle_signal(self, signum, frame):
        self.log.info(f"Sinal de SO recebido: {signum}")
        self.shutdown()

    def _handle_internal_shutdown(self, evento: Evento):
        self.log.info("Comando de Shutdown via EventBus.")
        self.shutdown()

    def start(self):
        self.log.info("Iniciando subsistemas...")
        
        # Inicia subsistemas
        for system in self._subsystems:
            try:
                name = getattr(system, 'name', system.__class__.__name__)
                self.log.info(f"Iniciando {name}...")
                system.start()
            except Exception as e:
                self.log.critical(f"Falha ao iniciar {system}: {e}")

        # Notificação de "Pronto"
        time.sleep(1) 
        bus.publicar(Evento(
            nome=Eventos.FALAR, 
            dados={"texto": "Sistemas online."}
        ))
        
        self.log.info("✅ KERNEL OPERACIONAL. Loop principal ativo.")
        
        try:
            while not self._shutdown_event.is_set():
                time.sleep(0.5)
        except KeyboardInterrupt:
            self.shutdown()
        finally:
            self.shutdown()

    def shutdown(self):
        if self._shutdown_event.is_set(): return
        self._shutdown_event.set()
        
        self.log.info("--- SHUTDOWN ---")
        for system in reversed(self._subsystems):
            try:
                system.stop()
            except Exception:
                pass
        
        # Mata processos zumbis se necessário
        time.sleep(1)
        self.log.info("Bye.")
        os._exit(0)

if __name__ == "__main__":
    kernel = JarvisKernel()
    kernel.bootstrap()
    kernel.start()