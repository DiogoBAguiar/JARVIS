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
from jarvis_system.hipocampo.reflexos import IntentionNormalizer
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AREA_BROCA_EARS")

# Constantes de Áudio (Ajustadas para performance/latência)
SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 4000
LIMIAR_SILENCIO = 0.015  # Ajustado para evitar disparos com ruído de fundo
BLOCOS_PAUSA_FIM = 5     # ~1.2 segundos de silêncio para considerar fim de frase
GANHO_MIC = 5.0          # Multiplicador digital de volume

class OuvidoBiologico:
    def __init__(self, model_size="base", device="cpu", compute_type="int8"):
        """
        Inicializa o subsistema de audição híbrido (Arquivo + Microfone).
        """
        logger.info(f"Inicializando Córtex Auditivo (Modelo: {model_size})...")
        
        self._stop_event = threading.Event()
        self._audio_queue = queue.Queue(maxsize=100) # Proteção contra estouro
        self._is_listening = False
        self._thread = None
        
        try:
            # 1. Carregamento do Modelo (Pesado)
            self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
            
            # 2. Conexão com Sistema Límbico (Reflexos)
            self.reflexos = IntentionNormalizer()
            
            # 3. Inscrição no Barramento de Eventos
            bus.inscrever(Eventos.STATUS_FALA, self._on_jarvis_speech_status)
            
            self._jarvis_speaking = False
            logger.info("Córtex Auditivo online. Integração: Reflexos + EventBus.")
            
        except Exception as e:
            logger.critical(f"Falha catastrófica na inicialização do Whisper: {e}")
            raise

    # ---------------------------------------------------------------------
    # MÉTODOS DE COMPATIBILIDADE COM O KERNEL (ADAPTER)
    # ---------------------------------------------------------------------
    def start(self):
        """Alias para iniciar() - exigido pelo Kernel do main.py."""
        self.iniciar()

    def stop(self):
        """Alias para parar() - exigido pelo Kernel do main.py."""
        self.parar()
    # ---------------------------------------------------------------------

    def _on_jarvis_speech_status(self, evento: Evento):
        """Callback para evitar que o Jarvis ouça a si mesmo."""
        self._jarvis_speaking = evento.dados.get("status", False)
        # status_str = "FALANDO (Surdez temporária)" if self._jarvis_speaking else "OUVINDO"

    def _audio_callback(self, indata, frames, time, status):
        """Callback de alta prioridade do SoundDevice."""
        if status:
            logger.warning(f"Status de áudio: {status}")
        
        if not self._jarvis_speaking:
            try:
                self._audio_queue.put_nowait(indata.copy())
            except queue.Full:
                pass # Descarta frames se a fila encher

    def _processar_audio_buffer(self, buffer_float):
        """Processa o buffer acumulado de áudio e transcreve."""
        if len(buffer_float) == 0:
            return

        try:
            # Concatena e transcreve
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
                if segment.no_speech_prob < 0.6: # Filtro de confiança
                    texto_acumulado.append(segment.text)

            texto_bruto = " ".join(texto_acumulado).strip()

            if texto_bruto:
                # --- CHECKPOINT DE REFLEXOS ---
                texto_corrigido = self.reflexos.corrigir_texto(texto_bruto)
                
                if texto_corrigido:
                    logger.info(f"👂 Ouvido: '{texto_corrigido}'")
                    # Publica para o Cérebro
                    bus.publicar(Evento(Eventos.FALA_RECONHECIDA, {"texto": texto_corrigido}))
                else:
                    logger.debug(f"Áudio descartado (Reflexo/Blacklist): '{texto_bruto}'")

        except Exception as e:
            logger.error(f"Erro na transcrição: {e}")

    def _worker_loop(self):
        """Loop principal de processamento de áudio (Thread separada)."""
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

                # Normalização e VAD
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
                        print() # Quebra linha da barra de volume
                        logger.debug("Silêncio detectado. Processando frase...")
                        self._processar_audio_buffer(buffer_frase)
                        
                        buffer_frase = []
                        falando = False
                        blocos_silencio = 0

    def _print_volume_bar(self, volume, falando):
        """Visualização simples de volume no console."""
        bar_len = int(min(volume, 1.0) * 20)
        bar = "█" * bar_len
        espaco = " " * (20 - bar_len)
        estado = "🔴 GRAVANDO" if falando else "💤 AGUARDANDO"
        if self._jarvis_speaking: estado = "🔇 JARVIS FALANDO"
        
        sys.stdout.write(f"\r🎤 Vol: {volume:.3f} |{bar}{espaco}| {estado}")
        sys.stdout.flush()

    def iniciar(self):
        """Inicia a thread de escuta em background."""
        if not self._thread or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._worker_loop, name="BrocaWorker", daemon=True)
            self._thread.start()
            logger.info("Serviço de audição iniciado.")

    def parar(self):
        """Encerra a thread de escuta graciosamente."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info("Serviço de audição encerrado.")

    def ouvir_arquivo(self, audio_path: str) -> str:
        """Processa um arquivo estático (útil para debug)."""
        if not os.path.exists(audio_path): return ""
        try:
            segments, _ = self.model.transcribe(audio_path, language="pt", beam_size=5)
            full_text = " ".join([s.text for s in segments])
            return self.reflexos.corrigir_texto(full_text)
        except Exception as e:
            logger.error(f"Erro em ouvir_arquivo: {e}")
            return ""

# ---------------------------------------------------------------------
# EXPORTAÇÃO PARA O MAIN.PY (ESSENCIAL)
# ---------------------------------------------------------------------
# Instanciamos a variável 'ears' no escopo global para que o main.py a encontre.
try:
    logger.info("🔧 Instanciando singleton 'ears' para o Sistema...")
    # Use 'base' para equilíbrio ou 'small' para melhor precisão
    ears = OuvidoBiologico(model_size="base", device="cpu")
except Exception as e:
    logger.error(f"❌ Erro ao instanciar OuvidoBiologico: {e}")
    ears = None

# ---------------------------------------------------------------------
# BLOCO DE TESTE
# ---------------------------------------------------------------------
if __name__ == "__main__":
    try:
        if ears is None:
            ears = OuvidoBiologico(model_size="tiny") 
            
        print("\n--- INICIANDO TESTE DE MICROFONE (CTRL+C para sair) ---")
        ears.iniciar()
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nInterrupção do usuário.")
        if ears: ears.parar()