import os
import sys
import json
import queue
import threading
import sounddevice as sd
import vosk
from typing import Optional

from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento  # <--- Adicionado 'Evento'
from jarvis_system.protocol import Eventos

# Configurações de Áudio
SAMPLE_RATE = 16000
BLOCK_SIZE = 8000
CHANNELS = 1
MODEL_PATH = "jarvis_system/area_broca/model"

log = JarvisLogger("BROCA_EARS")

class ListenService:
    """
    Serviço de Audição Offline (Vosk).
    """
    def __init__(self):
        self._queue: queue.Queue = queue.Queue()
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._recognizer: Optional[vosk.KaldiRecognizer] = None
        
        self._load_model()

    def _load_model(self):
        if not os.path.exists(MODEL_PATH):
            log.error(f"Modelo VOSK não encontrado em: {MODEL_PATH}")
            return

        try:
            log.info("Carregando modelo neural auditivo...")
            model = vosk.Model(MODEL_PATH)
            self._recognizer = vosk.KaldiRecognizer(model, SAMPLE_RATE)
            self._recognizer.SetWords(False)
            log.info("Sistema auditivo online.")
        except Exception as e:
            log.error("Falha catastrófica ao iniciar córtex auditivo", error=str(e))

    def _callback(self, indata, frames, time, status):
        if status:
            log.warning(f"Drop de frames de áudio: {status}")
        self._queue.put(bytes(indata))

    def _listen_loop(self):
        log.info("Microfone aberto. Escutando...")
        
        try:
            with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE, device=None,
                                   dtype='int16', channels=CHANNELS, callback=self._callback):
                
                while self._running:
                    try:
                        data = self._queue.get(timeout=1.0)
                    except queue.Empty:
                        continue

                    if self._recognizer.AcceptWaveform(data):
                        result = json.loads(self._recognizer.Result())
                        text = result.get("text", "").strip()
                        
                        if text:
                            log.info(f"Ouvido: '{text}'")
                            
                            # --- CORREÇÃO CRÍTICA AQUI ---
                            # Encapsula no objeto Evento e usa o método correto .publicar()
                            evento_fala = Evento(
                                nome=Eventos.FALA_RECONHECIDA, 
                                dados={"texto": text}
                            )
                            bus.publicar(evento_fala)

        except Exception as e:
            log.error("Erro no loop de áudio", error=str(e))
            self._running = False

    def start(self):
        if not self._recognizer:
            log.error("Não é possível iniciar: Modelo não carregado.")
            return

        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, name="BrocaListenThread", daemon=True)
        self._thread.start()
        log.debug("Thread de audição iniciada.")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        log.info("Serviço de audição encerrado.")

ears = ListenService()