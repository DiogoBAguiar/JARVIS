import sys
import signal
import threading
import time
import os
from typing import List, Protocol
from dotenv import load_dotenv

# --- CONFIGURAÇÃO DE AMBIENTE ---
# Força o carregamento do .env da raiz
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '../..'))
env_path = os.path.join(root_dir, '.env')
load_dotenv(env_path, override=True)

# --- IMPORTS DO SISTEMA (Caminhos Absolutos) ---
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos
from jarvis_system.cortex_frontal.orchestrator import Orchestrator

# Integração do Subconsciente
try:
    from jarvis_system.hipocampo.subconsciente import Subconsciente
except ImportError:
    Subconsciente = None

try:
    from jarvis_system.cortex_visual import vision
except ImportError as e:
    print(f"⚠️ AVISO: Módulo de Visão não carregado. Motivo: {e}")
    vision = None
except Exception as e:
    print(f"⚠️ AVISO: Erro crítico ao importar Visão: {e}")
    vision = None

class Subsystem(Protocol):
    def start(self) -> None: ...
    def stop(self) -> None: ...

class JarvisKernel:
    _instance = None

    # Singleton Real
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JarvisKernel, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized: return
        self.log = JarvisLogger("KERNEL")
        self._shutdown_event = threading.Event()
        self._subsystems: List[Subsystem] = []
        self.brain = None
        self.mouth = None
        self.ears = None
        self.eyes = None # NOVO: Olhos
        self._initialized = True

    def bootstrap(self):
        """Inicialização e Injeção de Dependências."""
        self.log.info("--- BOOTSTRAP: J.A.R.V.I.S. (Unified Core) ---")
        
        # 0. Sonhos
        if Subconsciente:
            try:
                self.log.info("💤 Ciclo REM (Subconsciente)...")
                sub = Subconsciente()
                sub.sonhar()
            except Exception as e:
                self.log.error(f"Falha no sonho: {e}")

        # 1. Carrega Drivers
        self.mouth = self._load_module('jarvis_system.area_broca.speak', 'mouth')
        self.ears = self._load_module('jarvis_system.area_broca.listen', 'ears')
        
        # 2. Carrega Cérebro
        try:
            self.brain = Orchestrator()
            self._register_subsystem(self.brain)
            self.log.info("🧠 Córtex Frontal Acoplado.")
        except Exception as e:
            self.log.critical(f"❌ Falha no Orquestrador: {e}")

        # 3. Registra Sentidos Básicos
        if self.mouth: 
            self.mouth.name = "Sistema de Fala"
            self._register_subsystem(self.mouth)
        if self.ears: 
            self.ears.name = "Sistema Auditivo"
            self._register_subsystem(self.ears)

        # 4. Carrega Visão (NOVO)
        if vision:
            try:
                self.eyes = vision
                self.eyes.name = "Córtex Visual"
                self._register_subsystem(self.eyes)
                self.log.info("👁️ Córtex Visual Acoplado.")
            except Exception as e:
                self.log.error(f"❌ Falha ao carregar visão: {e}")

        self._setup_event_bus()

    def start_background(self):
        """Inicia os subsistemas mas RETORNA o controle (para a API rodar)."""
        self.log.info("🚀 Iniciando subsistemas em background...")
        
        for system in self._subsystems:
            try:
                name = getattr(system, 'name', system.__class__.__name__)
                self.log.info(f"Iniciando {name}...")
                system.start()
            except Exception as e:
                self.log.critical(f"Falha ao iniciar {system}: {e}")
        
        self.log.info("✅ KERNEL OPERACIONAL (Modo Não-Bloqueante).")

    def shutdown(self):
        if self._shutdown_event.is_set(): return
        self._shutdown_event.set()
        self.log.info("--- SHUTDOWN ---")
        for system in reversed(self._subsystems):
            try:
                system.stop()
            except: pass
        self.log.info("Bye.")

    # --- Utilitários ---
    def _load_module(self, path: str, attr_name: str):
        try:
            module = __import__(path, fromlist=[attr_name])
            return getattr(module, attr_name)
        except Exception as e:
            self.log.warning(f"Erro carregando {attr_name}: {e}")
            return None

    def _register_subsystem(self, system):
        self._subsystems.append(system)

    def _setup_event_bus(self):
        bus.inscrever(Eventos.SHUTDOWN, lambda e: self.shutdown())

# Instância Global
kernel = JarvisKernel()