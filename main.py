import time
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos
from jarvis_system.area_broca.listen import ears
from jarvis_system.area_broca.speak import mouth
# Importa o novo cérebro (Isso já instancia a classe e registra os eventos)
from jarvis_system.cortex_frontal import orchestrator 
import jarvis_system.cortex_motor.os_actions

log = JarvisLogger("SYSTEM_ROOT")

def wake_up():
    log.info("--- INICIANDO JARVIS (Arquitetura Cognitiva v1) ---")
    
    # Nota: Não precisamos mais inscrever funções manualmente aqui.
    # Os módulos (ears, mouth, orchestrator) se auto-registram ao serem importados/iniciados.
    
    # Ativa Sensores
    ears.start()
    
    # Sinal de Vida
    bus.publicar(Evento(
        nome=Eventos.FALAR, 
        dados={"texto": "Córtex Frontal conectado. Aguardando ordens."}
    ))
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Interrupção manual detectada.")
        ears.stop()
        log.info("JARVIS Offline.")

if __name__ == "__main__":
    wake_up()