import sys
import signal
import threading
import os
import time
from dotenv import load_dotenv

# Carrega ambiente
load_dotenv()

# Imports do Core
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos

# Subsistemas (Orquestrador e Ações de SO)
import jarvis_system.cortex_frontal.orchestrator 
# import jarvis_system.cortex_motor.os_actions # Descomente quando criar este arquivo

# --- IMPORTAÇÃO DOS SENTIDOS (COM TRATAMENTO DE ERRO) ---
try:
    from jarvis_system.area_broca.listen import ears
except ImportError:
    print("⚠️  AVISO: Módulo de audição (listen.py) não encontrado.")
    ears = None

try:
    from jarvis_system.area_broca.speak import mouth
except ImportError:
    print("⚠️  AVISO: Módulo de fala (speak.py) não encontrado.")
    mouth = None

log = JarvisLogger("SYSTEM_KERNEL")

# Evento para controlar o loop principal
shutdown_event = threading.Event()

def system_check():
    """Diagnóstico rápido"""
    required_vars = ["GROQ_API_KEY", "JARVIS_MODEL_LOCAL"]
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        log.warning(f"⚠️  Variáveis ausentes: {missing}. Sistema instável.")
    else:
        log.info("✅ Variáveis de ambiente verificadas.")

def signal_handler(signum, frame):
    """Captura Ctrl+C"""
    log.info(f"\nSinal de interrupção ({signum}). Encerrando...")
    shutdown_event.set()

def on_internal_shutdown(evento: Evento):
    """Captura comando de voz 'Desligar'"""
    log.info("Recebido sinal de desligamento via Voz/Sistema.")
    shutdown_event.set()

def wake_up():
    log.info("--- INICIANDO JARVIS (Arquitetura Cognitiva v1) ---")
    
    system_check()

    # Registra manipuladores de sinal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Ouve evento de desligamento interno
    bus.inscrever(Eventos.SHUTDOWN, on_internal_shutdown)

    try:
        # 1. Ativa a Fala (Boca) - Para ele poder dizer que está on
        if mouth:
            mouth.start()

        # 2. Ativa a Audição (Ouvido)
        if ears:
            ears.start() 
        
        # 3. Feedback Inicial
        time.sleep(1) # Espera subsistemas subirem
        bus.publicar(Evento(
            nome=Eventos.FALAR, 
            dados={"texto": "Sistemas online. Estou ouvindo."}
        ))
        
        # 4. Loop Principal (CORRIGIDO PARA WINDOWS)
        # O .wait() puro bloqueia sinais no Windows. O loop com sleep resolve.
        log.info("KERNEL OPERACIONAL. Pressione Ctrl+C para encerrar.")
        
        while not shutdown_event.is_set():
            time.sleep(0.5) # Respira para permitir interrupção

    except KeyboardInterrupt:
        log.info("\nInterrupção manual detectada.")
        shutdown_event.set()
    except Exception as e:
        log.critical(f"Erro fatal no Kernel: {e}")
    
    finally:
        # 5. Rotina de Desligamento Limpa
        log.info("Desativando sensores...")
        shutdown_event.set()
        
        if ears: ears.stop()
        if mouth: mouth.stop()
        
        log.info("JARVIS Offline.")
        # Força bruta para matar threads de áudio persistentes
        os._exit(0)

if __name__ == "__main__":
    wake_up()