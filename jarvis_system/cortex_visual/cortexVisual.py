import time
import threading
import multiprocessing
import cv2
from multiprocessing import Queue, Event
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento as JarvisEvento
from .configVisao import FACE_CHECK_INTERVAL

log = JarvisLogger("CORTEX_VISUAL")

def vision_worker(queue_out, video_queue, telemetry_queue, stop_event):
    eyes = None
    try:
        from .cameraDriver import CameraDriver
        from .face_id import BiometricSystem
        
        # Inicializa Hardware
        eyes = CameraDriver()
        face_id = BiometricSystem()
        eyes.start()

        # Tenta carregar sensor de mãos
        try:
            from .hand_sensor import HandSensor
            hand_sensor = HandSensor()
        except Exception:
            hand_sensor = None

        last_face_check = 0
        last_seen_cache = {}
        
        # Log de confirmação apenas se tudo carregou
        if eyes and face_id:
            log.info("👁️ Processo Visual Online e Fluido.")

        while not stop_event.is_set():
            start_time = time.time()
            frame = eyes.get_frame()
            if frame is None: continue

            # RECONHECIMENTO (A cada intervalo)
            if (start_time - last_face_check) > FACE_CHECK_INTERVAL:
                nomes, _ = face_id.identify(frame)
                last_face_check = start_time
                for nome in nomes:
                    now = time.time()
                    if (now - last_seen_cache.get(nome, 0)) > 60:
                        queue_out.put(("ROSTO_IDENTIFICADO", nome))
                        last_seen_cache[nome] = now
            else:
                # Desenho contínuo nos frames intermediários
                face_id.identify(frame)

            # GESTOS
            gesto_atual = "---"
            if hand_sensor:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                gesto = hand_sensor.processar(rgb)
                if gesto:
                    gesto_atual = gesto
                    if gesto in ["PARE", "ROCK"]: queue_out.put(("GESTO_DETECTADO", gesto))

            # TRANSMISSÃO
            if video_queue and not video_queue.full():
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50]) # Qualidade 50 para performance
                if ret: video_queue.put(buffer.tobytes())

            if telemetry_queue and not telemetry_queue.full():
                telemetry_queue.put({"fps": 30, "hand": {"gesture": gesto_atual, "x":0, "y":0}})

            time.sleep(0.01)

    except KeyboardInterrupt:
        pass # Sai silenciosamente
    except Exception as e:
        log.error(f"Erro fatal no worker: {e}")
    finally:
        # ✅ CORREÇÃO: Protege o desligamento da câmera contra CTRL+C repetido
        try:
            if eyes: eyes.stop()
        except (KeyboardInterrupt, Exception):
            pass
        print("👁️ Processo Visual Encerrado.")

class VisualCortex:
    def __init__(self, video_queue=None, telemetry_queue=None):
        self.process = None
        self.queue = Queue()
        self.stop_event = multiprocessing.Event()
        self.video_queue = video_queue
        self.telemetry_queue = telemetry_queue
        self.running = False

    def start(self):
        log.info("👁️ Iniciando Córtex Visual...")
        self.stop_event.clear()
        self.process = multiprocessing.Process(
            target=vision_worker, 
            args=(self.queue, self.video_queue, self.telemetry_queue, self.stop_event),
            name="Jarvis_Vision_Core"
        )
        self.process.daemon = True
        self.process.start()
        self.running = True
        threading.Thread(target=self._listen_queue, daemon=True).start()

    def _listen_queue(self):
        while self.running:
            try:
                tipo, dado = self.queue.get(timeout=1)
                if tipo == "ROSTO_IDENTIFICADO":
                    bus.publicar(JarvisEvento("VISAO_ROSTO_IDENTIFICADO", {"nome": dado}))
                elif tipo == "GESTO_DETECTADO":
                    bus.publicar(JarvisEvento("VISAO_GESTO", {"gesto": dado}))
            except: continue

    def stop(self):
        self.running = False
        self.stop_event.set()
        if self.process: self.process.join(timeout=2)

vision = VisualCortex()