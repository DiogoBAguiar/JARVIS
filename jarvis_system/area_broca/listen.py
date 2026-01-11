import os
import json
import queue
import threading
import time
import re
import numpy as np
import sounddevice as sd
# import noisereduce as nr  <-- Desativado para reduzir latência
from faster_whisper import WhisperModel

# Core Imports
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos

# --- INTEGRAÇÃO COM MEMÓRIA ---
# Importamos o módulo de reflexos que consertamos anteriormente.
# Ele já gerencia a criação dos arquivos JSON se não existirem.
try:
    from jarvis_system.hipocampo.reflexos import reflexos
except ImportError:
    # Fallback apenas se o arquivo reflexos.py sumir (não deve acontecer)
    class ReflexosMock:
        def corrigir(self, t): return t
    reflexos = ReflexosMock()

# --- CONFIGURAÇÃO DE ÁUDIO ---
SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 4000 
# Ajuste de sensibilidade:
# 0.005 = Muito sensível (pega respiração)
# 0.015 = Pouco sensível (precisa falar alto)
LIMIAR_SILENCIO = 0.008 
GANHO_MIC = 10.0
# Blocos de silêncio para considerar fim de frase (aprox 1.5s)
BLOCOS_PAUSA_FIM = 6 

def get_initial_prompt():
    """Gera o prompt de contexto baseado na memória do Jarvis."""
    # Tenta ler as palavras-chave do arquivo JSON para enviesar o modelo
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = os.path.join(base_dir, "data", "speech_config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                apps = data.get("known_apps", [])
                wake = data.get("wake_words", [])
                # Junta tudo numa lista de dicas
                palavras = ", ".join(wake + apps + ["Tocar", "Abrir", "Pausar", "Volume", "Spotify"])
                return f"Contexto: Assistente Virtual. Vocabulário: {palavras}."
    except:
        pass
    return "Contexto: Assistente Virtual Brasileiro. Comandos: Tocar, Abrir, Pausar."

PROMPT_ATUAL = get_initial_prompt()

class IntentionNormalizer:
    def __init__(self, logger: JarvisLogger):
        self.log = logger
        # Lista negra de alucinações comuns do Whisper em silêncio
        self.hallucinations = [
            "legendas pela comunidade", 
            "amara.org", 
            "legendado por", 
            "subtitles by", 
            "todos os direitos reservados", 
            "transcrição",
            "mbc", 
            "auxiliary", 
            "copyright", 
            "encerrado o episódio",
            "assinem o canal",
            "ativem o sininho",
            "deixe seu like"
        ]

    def process(self, text: str):
        if not text or len(text.strip()) < 2: return
        
        text_lower = text.lower()
        
        # 1. Filtro de Alucinação
        for h in self.hallucinations:
            if h in text_lower:
                # Se for alucinação, ignoramos silenciosamente
                return

        # 2. Correção Fonética (A Mágica acontece aqui)
        # O reflexos.py vai trocar "Freigilson" por "Frei Gilson"
        clean_text = self._apply_phonetic_fix(text)
        
        # 3. Envio para o Cérebro
        self._clear_line()
        self.log.info(f"🧩 INTENÇÃO RECONHECIDA: '{clean_text}'")
        bus.publicar(Evento(Eventos.FALA_RECONHECIDA, {"texto": clean_text}))

    def _apply_phonetic_fix(self, text: str) -> str:
        text = text.strip()
        # Remove pontuação excessiva
        text = text.replace('.', '').replace(',', '').replace('?', '').replace('!', '')
        
        # Chama o módulo de reflexos (JSON/Memória RAM)
        return reflexos.corrigir(text)

    def _clear_line(self):
        print("\r" + " " * 100 + "\r", end="")

class WhisperListenService:
    def __init__(self):
        self.log = JarvisLogger("BROCA_EARS")
        self.normalizer = IntentionNormalizer(self.log)
        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread = None
        self.model = None
        self._is_jarvis_speaking = False
        
        bus.inscrever(Eventos.STATUS_FALA, self._on_speech_status)
        self._load_model()

    def _load_model(self):
        self.log.info("⏳ Carregando modelo Whisper (Small Int8)...")
        try:
            self.model = WhisperModel("small", device="cpu", compute_type="int8")
            self.log.info("✅ Whisper Pronto (VAD Híbrido Ativo).")
        except Exception as e:
            self.log.critical(f"Falha ao carregar Whisper: {e}")

    def _on_speech_status(self, evento: Evento):
        """Pausa o ouvido quando o Jarvis está falando."""
        status_anterior = self._is_jarvis_speaking
        self._is_jarvis_speaking = evento.dados.get("status", False)
        
        if self._is_jarvis_speaking and not status_anterior:
            self._clear_line()
            print("🛑 JARVIS FALANDO (Ouvido Pausado)...")
            with self._queue.mutex:
                self._queue.queue.clear()
        elif not self._is_jarvis_speaking and status_anterior:
            print("👂 Ouvido Reativado.")

    def _audio_callback(self, indata, frames, time, status):
        self._queue.put(indata.copy())

    def _clear_line(self):
        print("\r" + " " * 100 + "\r", end="")

    def _worker(self):
        self.log.info(f"👂 Monitorando (Gain={GANHO_MIC}x | Limiar={LIMIAR_SILENCIO})...")
        
        buffer_frase = []
        blocos_silencio = 0
        falando = False
        
        with sd.InputStream(samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE, 
                            channels=CHANNELS, callback=self._audio_callback, dtype='int16'):
            
            while not self._stop_event.is_set():
                try:
                    chunk_int16 = self._queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                if self._is_jarvis_speaking:
                    buffer_frase = []
                    falando = False
                    continue

                # Normalização
                chunk_float = ((chunk_int16.astype(np.float32) / 32768.0) * GANHO_MIC).flatten()
                volume = np.linalg.norm(chunk_float) / np.sqrt(len(chunk_float))
                
                # Visualização
                bar_len = int(min(volume, 1.0) * 20)
                bar = "█" * bar_len
                espaco = " " * (20 - bar_len)
                estado_visual = "🔴 REC" if falando else "💤 IDLE"
                if volume > LIMIAR_SILENCIO: estado_visual = "🟢 DETECT"

                print(f"\r🎤 Vol: {volume:.3f} |{bar}{espaco}| {estado_visual}", end="", flush=True)

                # Lógica VAD
                if volume > LIMIAR_SILENCIO:
                    if not falando: falando = True
                    blocos_silencio = 0
                    buffer_frase.append(chunk_float)
                
                elif falando:
                    buffer_frase.append(chunk_float)
                    blocos_silencio += 1
                    
                    if blocos_silencio > BLOCOS_PAUSA_FIM:
                        self._clear_line()
                        self.log.info("⏳ Processando áudio capturado...")
                        
                        if len(buffer_frase) > 0:
                            audio_final = np.concatenate(buffer_frase)
                            self._transcrever(audio_final)
                        
                        buffer_frase = []
                        falando = False
                        blocos_silencio = 0

    def _transcrever(self, audio_data):
        try:
            # Whisper com VAD interno ativado
            segments, info = self.model.transcribe(
                audio_data, 
                beam_size=5, 
                language="pt",
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
                initial_prompt=PROMPT_ATUAL, # Usa o prompt com vocabulário atualizado
                condition_on_previous_text=False
            )
            
            texto_final = " ".join([s.text for s in segments]).strip()
            
            if texto_final:
                self._clear_line()
                self.log.info(f"📝 Whisper ouviu: '{texto_final}'")
                self.normalizer.process(texto_final)
                
        except Exception as e:
            self.log.error(f"Erro transcrição: {e}")

    def start(self):
        if not self._thread or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._worker, name="BrocaListener", daemon=True)
            self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)

# Instância Global
ears = WhisperListenService()

if __name__ == "__main__":
    print("Iniciando teste de microfone...")
    ears.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        ears.stop()
        print("Encerrando.")