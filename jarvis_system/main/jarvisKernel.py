import sys
import signal
import threading
import multiprocessing # <--- Importante para as Filas
import time
import os # <--- Importante para forçar o fecho (os._exit)
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

# Importação da Visão (Corrigido para usar a classe VisualCortex)
try:
    from jarvis_system.cortex_visual.cortexVisual import VisualCortex
except ImportError as e:
    print(f"⚠️ AVISO: Módulo de Visão não carregado. Motivo: {e}")
    VisualCortex = None
except Exception as e:
    print(f"⚠️ AVISO: Erro crítico ao importar Visão: {e}")
    VisualCortex = None

class Subsystem(Protocol):
    def start(self) -> None: ...
    def stop(self) -> None: ...

class JarvisKernel:
    _instance = None
    _initialized = False # Flag de classe para garantir init único

    # Singleton Real
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JarvisKernel, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Evita re-inicialização se chamado múltiplas vezes
        if self._initialized: return
        
        self.log = JarvisLogger("KERNEL")
        self._shutdown_event = threading.Event()
        self._subsystems: List[Subsystem] = []
        
        # Componentes Principais
        self.brain = None
        self.mouth = None
        self.ears = None
        self.eyes = None 

        # -----------------------------------------------------------------
        # 🌉 PONTES DE DADOS (QUEUES) PARA O FRONT-END
        # -----------------------------------------------------------------
        # Fila para o Vídeo (MJPEG Stream) - Max 2 frames para ser live
        self.video_queue = multiprocessing.Queue(maxsize=2)
        
        # Fila para Dados (Gestos, FPS, Confiança) - Max 10 eventos
        self.telemetry_queue = multiprocessing.Queue(maxsize=10)
        # -----------------------------------------------------------------

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

        # 1. Carrega Drivers de Áudio
        # Nota: Ajusta o path se necessário, assumindo que __init__ expõe a classe principal
        try:
            from jarvis_system.area_broca.speak import mouth
            self.mouth = mouth
        except:
            self.mouth = None
            
        try:
            from jarvis_system.area_broca.listen import ears
            self.ears = ears
        except:
            self.ears = None
        
        # 2. Carrega Cérebro
        try:
            self.brain = Orchestrator()
            self._register_subsystem(self.brain)
            self.log.info("🧠 Córtex Frontal Acoplado.")
        except Exception as e:
            self.log.critical(f"❌ Falha no Orquestrador: {e}")

        # 3. Registra Sentidos Básicos
        if self.mouth: 
            # Verifica se tem atributo 'name', senão define
            if not hasattr(self.mouth, 'name'): self.mouth.name = "Sistema de Fala"
            self._register_subsystem(self.mouth)
            
        if self.ears: 
            if not hasattr(self.ears, 'name'): self.ears.name = "Sistema Auditivo"
            self._register_subsystem(self.ears)

        # 4. Carrega Visão (COM FILAS)
        if VisualCortex:
            try:
                # Injetamos as filas no construtor da visão
                self.eyes = VisualCortex(
                    video_queue=self.video_queue,
                    telemetry_queue=self.telemetry_queue
                )
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
                # Tenta pegar o nome ou usa o nome da classe
                name = getattr(system, 'name', system.__class__.__name__)
                self.log.info(f"Iniciando {name}...")
                
                # Se o sistema tiver start(), chama
                if hasattr(system, 'start'):
                    system.start()
            except Exception as e:
                self.log.critical(f"Falha ao iniciar {system}: {e}")
        
        self.log.info("✅ KERNEL OPERACIONAL (Modo Não-Bloqueante).")

    def shutdown(self):
        """Encerra graciosamente os sistemas e força a saída se houver bloqueios."""
        if self._shutdown_event.is_set(): return
        self._shutdown_event.set()
        self.log.info("--- SHUTDOWN ---")
        
        # 1. Garante de forma explícita que a Visão liberta a Câmara antes de tudo
        if hasattr(self, 'eyes') and self.eyes:
            try:
                self.eyes.stop()
            except: 
                pass

        # 2. Para os restantes sistemas de trás para a frente
        for system in reversed(self._subsystems):
            try:
                if hasattr(system, 'stop'):
                    system.stop()
            except: 
                pass
            
        self.log.info("Bye.")
        
        # 3. BALA DE PRATA: Mata o processo principal imediatamente devolvendo o terminal ao utilizador
        os._exit(0)

    def _register_subsystem(self, system):
        self._subsystems.append(system)

    def _setup_event_bus(self):
        bus.inscrever(Eventos.SHUTDOWN, lambda e: self.shutdown())

# Instância Global
kernel = JarvisKernel()