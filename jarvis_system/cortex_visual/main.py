import time
import threading
import multiprocessing
from multiprocessing import Queue, Event

# Imports do sistema principal (só para log e bus)
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento as JarvisEvento
from .config import FACE_CHECK_INTERVAL

log = JarvisLogger("CORTEX_VISUAL")

def vision_worker(queue_out, stop_event):
    """
    ESTA FUNÇÃO RODA EM OUTRO NÚCLEO DA CPU (Processo Isolado).
    Ela não compartilha memória com o Jarvis principal.
    """
    # Importar AQUI DENTRO para não travar o processo principal
    # e garantir que cada processo tenha sua própria instância do dlib
    from .eyes import CameraDriver
    from .face_id import BiometricSystem
    
    # Inicializa os sistemas no novo núcleo
    eyes = CameraDriver()
    face_id = BiometricSystem()
    
    eyes.start()
    last_seen_cache = {}

    while not stop_event.is_set():
        start_time = time.time()
        
        # 1. Captura (Rápida)
        frame = eyes.get_frame()
        
        if frame is not None:
            # 2. Processamento Pesado (Aqui o GIL não atrapalha o áudio!)
            nomes = face_id.identify(frame)
            
            if nomes:
                # Envia para o processo principal via Fila
                for nome in nomes:
                    # Cache local simples para não inundar a fila
                    now = time.time()
                    if (now - last_seen_cache.get(nome, 0)) > 60:
                        queue_out.put(("ROSTO_IDENTIFICADO", nome))
                        last_seen_cache[nome] = now

        # 3. Dorme o restante do intervalo (Economia de Energia)
        elapsed = time.time() - start_time
        sleep_time = max(0.1, FACE_CHECK_INTERVAL - elapsed)
        time.sleep(sleep_time)

    eyes.stop()
    print("👁️ Processo Visual Encerrado.")

class VisualCortex:
    def __init__(self):
        self.process = None
        self.queue = Queue()
        self.stop_event = multiprocessing.Event()
        self.listener_thread = None
        self.running = False

    def start(self):
        log.info("👁️ Inicializando Córtex Visual em MULTIPROCESSAMENTO...")
        
        # Cria o processo isolado
        self.stop_event.clear()
        self.process = multiprocessing.Process(
            target=vision_worker, 
            args=(self.queue, self.stop_event),
            name="Jarvis_Vision_Core"
        )
        self.process.daemon = True # Morre se o Jarvis morrer
        self.process.start()
        
        self.running = True
        
        # Thread leve no processo principal só para ouvir a fila
        self.listener_thread = threading.Thread(target=self._listen_queue, daemon=True)
        self.listener_thread.start()
        
        log.info(f"👁️ Visão rodando no PID: {self.process.pid} (Núcleo Dedicado)")

    def _listen_queue(self):
        """Fica no processo principal esperando mensagens do processo visual."""
        while self.running:
            try:
                # Bloqueia por 1s esperando algo, para não gastar CPU em loop
                tipo, dado = self.queue.get(timeout=1)
                
                if tipo == "ROSTO_IDENTIFICADO":
                    log.info(f"👤 Rosto recebido do núcleo visual: {dado}")
                    bus.publicar(JarvisEvento("VISAO_ROSTO_IDENTIFICADO", {
                        "nome": dado,
                        "confianca": "alta"
                    }))
                    
            except:
                # Queue vazia (timeout), volta pro loop
                continue

    def stop(self):
        self.running = False
        log.info("👁️ Parando processo visual...")
        self.stop_event.set()
        if self.process:
            self.process.join(timeout=5)
            if self.process.is_alive():
                self.process.terminate()

# Instância Global
vision = VisualCortex()