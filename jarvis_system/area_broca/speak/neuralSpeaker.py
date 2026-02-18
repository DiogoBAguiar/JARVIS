# jarvis_system/area_broca/speak/main.py
import threading
import queue
import os
import time
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos

try:
    from jarvis_system.cortex_frontal.voiceDirector import VoiceDirector
except ImportError:
    VoiceDirector = None

from .configSpeak import FISH_TAGS
from .audioEngine import AudioEngine
from .voiceIndexer import VoiceIndexer
from .fishSynthesizer import FishSynthesizer

class NeuralSpeaker:
    def __init__(self):
        self.log = JarvisLogger("BROCA_VOICE")
        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread = None
        
        # Sub-módulos
        base_dir = os.path.join(os.getcwd(), "jarvis_system", "data", "voices")
        self.engine = AudioEngine(self.log)
        self.indexer = VoiceIndexer(base_dir, self.log)
        self.synth = FishSynthesizer(self.log)
        self.voice_director = VoiceDirector() if VoiceDirector else None

        # Barramento
        bus.inscrever(Eventos.FALAR, self._adicionar_a_fila)
        self.log.info("🗣️ Área de Broca (Modular v3.0) Online.")

    def _adicionar_a_fila(self, evento: Evento):
        text = evento.dados.get("texto")
        if text: self._queue.put(text)

    def _process_text(self, text):
        key = self.indexer.normalize_key(text)
        
        # 1. Tenta Cache
        path, entry = self.indexer.get_path(key)
        if path:
            self.log.info(f"💾 Memória: {entry.get('id')}")
            self.engine.play_file(path, self._stop_event)
            return

        # 2. Aprende (Síntese)
        cat = self.indexer.determine_category(text)
        ctx = self.indexer.detect_context_temporal(text)
        sub = self.indexer.detect_sub_context(text, cat)
        new_id = self.indexer.generate_next_id(cat)
        
        # Analise de tom opcional
        emotion = "neutral"
        if self.voice_director:
            try: emotion = self.voice_director.analisar_tom(text)
            except: pass

        # Prepara caminhos
        filename = f"{new_id}.mp3"
        rel_dir = os.path.join("assets", cat, ctx, sub)
        abs_dir = os.path.join(self.indexer.base_dir, rel_dir)
        os.makedirs(abs_dir, exist_ok=True)
        out_path = os.path.join(abs_dir, filename)

        metadata = {
            "id": new_id,
            "text": text,
            "category": cat,
            "context": ctx,
            "sub_context": sub,
            "key_hash": key,
            "emotion": emotion,
            "file_path": os.path.join(rel_dir, filename).replace("\\", "/")
        }

        success = self.synth.synthesize(text, metadata, out_path)
        
        if success:
            self.indexer.save_entry(metadata)
            self.engine.play_file(out_path, self._stop_event)
        else:
            self.engine.speak_offline(text)

    def _worker(self):
        while not self._stop_event.is_set():
            try:
                text = self._queue.get(timeout=1.0)
                bus.publicar(Evento(Eventos.STATUS_FALA, {"status": True}))
                self._process_text(text)
                bus.publicar(Evento(Eventos.STATUS_FALA, {"status": False}))
                self._queue.task_done()
            except queue.Empty: continue
            except Exception as e:
                self.log.error(f"Worker Crash: {e}")

    def start(self):
        if not self._thread or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._worker, daemon=True)
            self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)