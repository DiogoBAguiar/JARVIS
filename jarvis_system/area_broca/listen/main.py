# jarvis_system/area_broca/listen/main.py
import threading
import queue
import time
import sys
import numpy as np
import logging

# Imports Internos
from jarvis_system.hipocampo.reflexos import reflexos
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos

# Módulos Locais
from .config import *
from .driver import AudioDriver
from .transcriber import WhisperTranscriber

# Configuração de Logs Local
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BROCA_EARS")

class OuvidoBiologico:
    def __init__(self, model_size="base", device="cpu"):
        logger.info("👂 Inicializando Sistema Auditivo Modular...")
        
        self._stop_event = threading.Event()
        self._audio_queue = queue.Queue()
        self._thread = None
        self._is_listening = False
        
        # Estado Global
        self._jarvis_speaking = False
        
        # Subsistemas
        self.driver = AudioDriver(SAMPLE_RATE, BLOCK_SIZE, CHANNELS)
        self.brain = WhisperTranscriber(model_size, device)
        self.reflexos = reflexos

        # Barramento
        bus.inscrever(Eventos.STATUS_FALA, self._on_jarvis_speech_status)

    def _on_jarvis_speech_status(self, evento: Evento):
        """Evita que o Jarvis ouça a si mesmo."""
        status_anterior = self._jarvis_speaking
        self._jarvis_speaking = evento.dados.get("status", False)
        
        if self._jarvis_speaking and not status_anterior:
            with self._audio_queue.mutex:
                self._audio_queue.queue.clear()

    def _audio_callback(self, indata, frames, time, status):
        """Callback de alta performance executado pelo Driver."""
        if status:
            logger.warning(f"⚠️ Status Driver: {status}")
        
        if not self._jarvis_speaking:
            self._audio_queue.put(indata.copy())

    def _process_transcription(self, buffer_frase):
        """Envia áudio para IA e trata o resultado."""
        texto_bruto = self.brain.transcribe(buffer_frase)
        
        if texto_bruto:
            texto_corrigido, ignorar = self.reflexos.processar_reflexo(texto_bruto)
            
            if not ignorar:
                logger.info(f"🗣️  Usuário: '{texto_corrigido}'")
                bus.publicar(Evento(Eventos.FALA_RECONHECIDA, {"texto": texto_corrigido}))
            else:
                logger.debug(f"🔇 Ignorado: '{texto_bruto}'")

    def _worker_loop(self):
        """Loop de VAD (Voice Activity Detection) e Processamento."""
        logger.info("🎤 Serviço de escuta ativo.")
        
        # Inicia Hardware
        self.driver.start_stream(self._audio_callback)
        
        buffer_frase = []
        blocos_silencio = 0
        falando = False
        
        while not self._stop_event.is_set():
            try:
                chunk_int16 = self._audio_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            # Processamento de Sinal (Normalização e Ganho)
            chunk_float = ((chunk_int16.astype(np.float32) / 32768.0) * GANHO_MIC).flatten()
            volume = np.linalg.norm(chunk_float) / np.sqrt(len(chunk_float))
            
            self._print_volume_bar(volume, falando)

            # Lógica VAD
            if volume > LIMIAR_SILENCIO:
                if not falando:
                    falando = True
                blocos_silencio = 0
                buffer_frase.append(chunk_float)
            
            elif falando:
                buffer_frase.append(chunk_float)
                blocos_silencio += 1
                
                if blocos_silencio > BLOCOS_PAUSA_FIM:
                    sys.stdout.write("\n")
                    sys.stdout.flush()
                    
                    self._process_transcription(buffer_frase)
                    
                    buffer_frase = []
                    falando = False
                    blocos_silencio = 0
        
        # Cleanup ao sair do loop
        self.driver.stop_stream()

    def _print_volume_bar(self, volume, falando):
        bar_len = int(min(volume, 1.0) * 20)
        bar = "█" * bar_len
        espaco = " " * (20 - bar_len)
        estado = "🔴 GRAVANDO" if falando else "💤 AGUARDANDO"
        if self._jarvis_speaking: estado = "🔇 JARVIS FALANDO"
        sys.stdout.write(f"\r🎤 Vol: {volume:.3f} |{bar}{espaco}| {estado}")
        sys.stdout.flush()

    def start(self):
        if not self._thread or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._worker_loop, name="BrocaListener", daemon=True)
            self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)