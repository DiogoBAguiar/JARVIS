import os
import sys
import logging
import time
import queue
import threading
import numpy as np
import sounddevice as sd

# Adicionando o diretório raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from faster_whisper import WhisperModel

# --- CORREÇÃO: Importar apenas o 'reflexos' (Singleton) ---
from jarvis_system.hipocampo.reflexos import reflexos
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AREA_BROCA_EARS")

# Constantes de Áudio
SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 4000
LIMIAR_SILENCIO = 0.015 
BLOCOS_PAUSA_FIM = 5    
GANHO_MIC = 5.0        

class OuvidoBiologico:
    def __init__(self, model_size="base", device="cpu", compute_type="int8"):
        """
        Inicializa o subsistema de audição híbrido.
        """
        logger.info(f"Inicializando Córtex Auditivo (Modelo: {model_size})...")
        
        self._stop_event = threading.Event()
        self._audio_queue = queue.Queue(maxsize=100)
        self._is_listening = False
        self._thread = None
        
        try:
            # 1. Carregamento do Modelo
            self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
            
            # 2. Conexão com Sistema Límbico (Usamos o Singleton global 'reflexos')
            # Não precisamos instanciar nada aqui, o 'reflexos' já vem pronto do import.
            self.reflexos = reflexos 
            
            # 3. Inscrição no Barramento de Eventos
            bus.inscrever(Eventos.STATUS_FALA, self._on_jarvis_speech_status)
            
            self._jarvis_speaking = False
            logger.info("Córtex Auditivo online. Integração: Reflexos + EventBus.")
            
        except Exception as e:
            logger.critical(f"Falha catastrófica na inicialização do Whisper: {e}")
            raise

    # ... (MÉTODOS START/STOP/CALLBACKS IGUAIS) ...
    def start(self): self.iniciar()
    def stop(self): self.parar()

    def _on_jarvis_speech_status(self, evento: Evento):
        self._jarvis_speaking = evento.dados.get("status", False)

    def _audio_callback(self, indata, frames, time, status):
        if status: logger.warning(f"Status de áudio: {status}")
        
        if not self._jarvis_speaking:
            try:
                self._audio_queue.put_nowait(indata.copy())
            except queue.Full:
                pass 

    def _processar_audio_buffer(self, buffer_float):
        """Processa o buffer acumulado e transcreve."""
        if len(buffer_float) == 0: return

        try:
            audio_final = np.concatenate(buffer_float)
            
            segments, info = self.model.transcribe(
                audio_final,
                beam_size=5,
                language="pt",
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
                condition_on_previous_text=False
            )

            texto_acumulado = []
            for segment in segments:
                if segment.no_speech_prob < 0.6:
                    texto_acumulado.append(segment.text)

            texto_bruto = " ".join(texto_acumulado).strip()

            if texto_bruto:
                # --- CHECKPOINT DE REFLEXOS ---
                # Aqui usamos o método novo da classe reflexos refatorada
                # O método agora retorna uma tupla (texto, deve_ignorar)
                texto_corrigido, ignorar = self.reflexos.processar_reflexo(texto_bruto)
                
                if not ignorar:
                    logger.info(f"👂 Ouvido: '{texto_corrigido}'")
                    bus.publicar(Evento(Eventos.FALA_RECONHECIDA, {"texto": texto_corrigido}))
                else:
                    logger.debug(f"🔇 Ignorado pelo Subconsciente: '{texto_bruto}'")

        except Exception as e:
            logger.error(f"Erro na transcrição: {e}")

    # ... (RESTO DO CÓDIGO DO WORKER LOOP E VISUALIZAÇÃO) ...
    def _worker_loop(self):
        logger.info("Iniciando loop de captura de áudio...")
        buffer_frase = []
        blocos_silencio = 0
        falando = False
        
        with sd.InputStream(samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE, 
                            channels=CHANNELS, callback=self._audio_callback, dtype='int16'):
            while not self._stop_event.is_set():
                try:
                    chunk_int16 = self._audio_queue.get(timeout=0.5) 
                except queue.Empty:
                    continue

                chunk_float = ((chunk_int16.astype(np.float32) / 32768.0) * GANHO_MIC).flatten()
                volume = np.linalg.norm(chunk_float) / np.sqrt(len(chunk_float))
                
                self._print_volume_bar(volume, falando)

                if volume > LIMIAR_SILENCIO:
                    if not falando:
                        falando = True
                    blocos_silencio = 0
                    buffer_frase.append(chunk_float)
                
                elif falando:
                    buffer_frase.append(chunk_float)
                    blocos_silencio += 1
                    
                    if blocos_silencio > BLOCOS_PAUSA_FIM:
                        print() 
                        self._processar_audio_buffer(buffer_frase)
                        buffer_frase = []
                        falando = False
                        blocos_silencio = 0

    def _print_volume_bar(self, volume, falando):
        bar_len = int(min(volume, 1.0) * 20)
        bar = "█" * bar_len
        espaco = " " * (20 - bar_len)
        estado = "🔴 GRAVANDO" if falando else "💤 AGUARDANDO"
        if self._jarvis_speaking: estado = "🔇 JARVIS FALANDO"
        sys.stdout.write(f"\r🎤 Vol: {volume:.3f} |{bar}{espaco}| {estado}")
        sys.stdout.flush()

    def iniciar(self):
        if not self._thread or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._worker_loop, name="BrocaWorker", daemon=True)
            self._thread.start()
            logger.info("Serviço de audição iniciado.")

    def parar(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info("Serviço de audição encerrado.")

# ---------------------------------------------------------------------
# EXPORTAÇÃO SINGLETON
# ---------------------------------------------------------------------
try:
    logger.info("🔧 Instanciando singleton 'ears'...")
    ears = OuvidoBiologico(model_size="base", device="cpu")
except Exception as e:
    logger.error(f"❌ Erro ao instanciar OuvidoBiologico: {e}")
    ears = None

if __name__ == "__main__":
    try:
        if ears is None:
            ears = OuvidoBiologico(model_size="tiny") 
        print("\n--- INICIANDO TESTE ---")
        ears.iniciar()
        while True: time.sleep(1)
    except KeyboardInterrupt:
        if ears: ears.parar()