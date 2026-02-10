import cv2
import threading
import time
from jarvis_system.cortex_frontal.observability import JarvisLogger
from .config import CAMERA_ID, FRAME_WIDTH, FRAME_HEIGHT

log = JarvisLogger("VISUAL_EYES")

class CameraDriver:
    def __init__(self):
        self.cap = None
        self.frame = None
        self.running = False
        self.lock = threading.Lock()
        
    def start(self):
        if self.running: return
        
        log.info(f"👁️ Abrindo câmera (ID: {CAMERA_ID})...")
        self.cap = cv2.VideoCapture(CAMERA_ID)
        
        # Configura resolução para ser leve
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        
        if not self.cap.isOpened():
            log.error("❌ Falha ao abrir dispositivo de vídeo.")
            return

        self.running = True
        # Inicia thread de captura contínua
        threading.Thread(target=self._update, daemon=True).start()
        log.info("👁️ Sistema visual online.")

    def _update(self):
        """Lê frames em loop numa thread separada."""
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = frame
            time.sleep(0.01) # ~30 FPS

    def get_frame(self):
        """Retorna o último frame capturado de forma thread-safe."""
        with self.lock:
            if self.frame is not None:
                return self.frame.copy()
        return None

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()
        log.info("👁️ Câmera fechada.")