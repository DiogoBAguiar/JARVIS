import os
import asyncio
import threading
import queue
import uuid
import time
import edge_tts
import pygame

# Imports do Sistema
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos

log = JarvisLogger("BROCA_VOICE")

# Configuração
VOICE = "pt-BR-AntonioNeural" 
RATE = "+10%"
PITCH = "+0Hz"

class SpeakService:
    def __init__(self):
        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread = None
        self._is_active = False
        
        try:
            pygame.mixer.init(frequency=24000, buffer=1024)
        except Exception as e:
            log.warning(f"Driver de áudio não detectado: {e}")

    def start(self):
        if self._is_active: return
        self._is_active = True
        self._stop_event.clear()
        bus.inscrever(Eventos.FALAR, self._queue_fala)
        self._thread = threading.Thread(target=self._worker_loop, name="VoiceWorker", daemon=True)
        self._thread.start()
        log.info(f"🔊 Córtex Vocal Ativo ({VOICE})")

    def stop(self):
        self._is_active = False
        self._stop_event.set()
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except: pass
        if self._thread:
            self._thread.join(timeout=2.0)
        log.info("🔇 Córtex Vocal Desligado.")

    def _queue_fala(self, evento):
        if not self._is_active: return
        texto = evento.dados.get("texto")
        if texto:
            self._queue.put(texto)

    def _worker_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while not self._stop_event.is_set():
            try:
                texto = self._queue.get(timeout=0.5)
                self._speak_now(texto, loop)
                self._queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                log.error(f"Erro no loop de voz: {e}")

        loop.close()

    def _speak_now(self, texto: str, loop):
        filename = f"tts_{uuid.uuid4().hex}.mp3"
        
        try:
            # --- AJUSTE VISUAL: MOSTRAR O QUE FALA NO TERMINAL ---
            log.info(f"🗣️  JARVIS DIZ: '{texto}'")
            # -----------------------------------------------------

            # 1. BLOQUEIO IMEDIATO (Evita ouvir a si mesmo)
            bus.publicar(Evento(Eventos.STATUS_FALA, {"status": True}))

            # 2. Geração (Demora ~1s)
            loop.run_until_complete(self._generate_audio(texto, filename))
            
            if not os.path.exists(filename): return

            # 3. Reprodução
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy() and not self._stop_event.is_set():
                time.sleep(0.1) 
            
            pygame.mixer.music.unload()

        except Exception as e:
            log.error(f"Falha ao falar '{texto}': {e}")
        
        finally:
            # 4. LIBERAÇÃO
            time.sleep(0.2) 
            bus.publicar(Evento(Eventos.STATUS_FALA, {"status": False}))
            self._safe_remove(filename)

    async def _generate_audio(self, text: str, filename: str):
        communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
        await communicate.save(filename)

    def _safe_remove(self, filename: str):
        for _ in range(3):
            try:
                if os.path.exists(filename):
                    os.remove(filename)
                break
            except PermissionError:
                time.sleep(0.2)
            except Exception:
                break

mouth = SpeakService()