import os
import json
import queue
import threading
import time
import wave
import re
import numpy as np
import sounddevice as sd
import noisereduce as nr
from faster_whisper import WhisperModel

# Core Imports
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos

# --- INTEGRAÇÃO COM MEMÓRIA DE REFLEXOS (Active Learning) ---
try:
    from jarvis_system.hipocampo.reflexos import reflexos
except ImportError:
    class ReflexosMock:
        def corrigir(self, t): return t
    reflexos = ReflexosMock()

# --- CONFIGURAÇÃO ---
SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 4000 

# --- AJUSTES DE SENSIBILIDADE ---
LIMIAR_SILENCIO = 0.005 
GANHO_MIC = 10.0
BLOCOS_PAUSA_FIM = 6 

def load_speech_config():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(base_dir, "data", "speech_config.json")
    
    defaults = {
        "wake_words": ["jarvis"],
        "confirmation_words": ["sim", "não"],
        "known_apps": ["chrome"],
        "phonetic_map": {}
    }

    if not os.path.exists(config_path): return defaults
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except: return defaults

CONFIG = load_speech_config()
CONFIRMATION_WORDS = CONFIG.get("confirmation_words", [])
PHONETIC_MAP = CONFIG.get("phonetic_map", {})
WAKE_WORDS = CONFIG.get("wake_words", [])

class IntentionNormalizer:
    def __init__(self, logger: JarvisLogger):
        self.log = logger
        # Frases que o Whisper alucina no silêncio
        self.hallucinations = [
            "legendas pela comunidade", 
            "amara.org", 
            "legendado por", 
            "subtitles by",
            "todos os direitos reservados",
            "estratégia mental",
            "você pode jogar",
            "editado por",
            "encerrado por"
        ]

    def process(self, text: str):
        if not text: return
        
        # 1. Filtro de Alucinação
        text_lower = text.lower()
        for h in self.hallucinations:
            if h in text_lower:
                self.log.debug(f"👻 Alucinação removida: '{text[:30]}...'")
                return

        # 2. Correção Fonética (Memória Estática + Aprendizado Dinâmico)
        clean_text = self._apply_phonetic_fix(text)
        
        # 3. ENVIA TUDO PARA O CÓRTEX
        # Removemos o bloqueio "_is_actionable". 
        # Agora o Orchestrator decide se ouve baseada na Janela de Atenção.
        if len(clean_text) > 1: # Ignora letras soltas
            self.log.info(f"🧩 INTENÇÃO ENVIADA: '{clean_text}'")
            bus.publicar(Evento(Eventos.FALA_RECONHECIDA, {"texto": clean_text}))

    def _apply_phonetic_fix(self, text: str) -> str:
        text = text.lower().strip()
        text = text.replace('.', '').replace(',', '').replace('?', '').replace('!', '')
        
        # AQUI É O PULO DO GATO:
        # Chama a memória dinâmica para corrigir erros aprendidos ("tocasho" -> "tocar")
        text = reflexos.corrigir(text)
        
        # Mantém compatibilidade com o phonetic_map estático do JSON (se houver sobras)
        sorted_map = sorted(PHONETIC_MAP.items(), key=lambda x: len(x[0]), reverse=True)
        
        for erro, correcao in sorted_map:
            if erro in text:
                pattern = r'(?<!\w)' + re.escape(erro) + r'(?!\w)'
                text = re.sub(pattern, correcao, text, flags=re.IGNORECASE)
                
        return text

    def _is_actionable(self, text: str) -> bool:
        # Mantido apenas para compatibilidade se necessário, mas não usado no fluxo principal agora
        if any(w in text for w in WAKE_WORDS): return True
        if text in CONFIRMATION_WORDS: return True
        return False

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
        self.log.info("⏳ Carregando modelo Whisper (Small)...")
        try:
            self.model = WhisperModel("small", device="cpu", compute_type="int8")
            self.log.info("✅ Whisper Pronto.")
        except Exception as e:
            self.log.critical(f"Falha Whisper: {e}")

    def _on_speech_status(self, evento: Evento):
        self._is_jarvis_speaking = evento.dados.get("status", False)
        if self._is_jarvis_speaking:
            with self._queue.mutex:
                self._queue.queue.clear()

    def _audio_callback(self, indata, frames, time, status):
        self._queue.put(indata.copy())

    def _save_debug_audio(self, audio_data, filename="debug_audio.wav"):
        try:
            audio_clipped = np.clip(audio_data, -1.0, 1.0)
            audio_int16 = (audio_clipped * 32767).astype(np.int16)
            with wave.open(filename, "wb") as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(audio_int16.tobytes())
        except Exception: pass

    def _worker(self):
        self.log.info(f"👂 Ouvido Ativo (Ganho {GANHO_MIC}x + Noise Reduction).")
        
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

                # 1. Normalização, Boost e FLATTEN
                chunk_float = ((chunk_int16.astype(np.float32) / 32768.0) * GANHO_MIC).flatten()

                # 2. VAD
                volume = np.linalg.norm(chunk_float) / np.sqrt(len(chunk_float))
                
                if volume > LIMIAR_SILENCIO:
                    bar = "█" * int(min(volume, 1.0) * 50) 
                    print(f"\r🔊 {volume:.3f} |{bar:<10}|", end="", flush=True)
                    
                    if not falando:
                        falando = True
                    blocos_silencio = 0
                    buffer_frase.append(chunk_float)
                
                elif falando:
                    buffer_frase.append(chunk_float)
                    blocos_silencio += 1
                    
                    if blocos_silencio > BLOCOS_PAUSA_FIM:
                        print("") 
                        self.log.info("⏳ Processando...")
                        
                        audio_sujo = np.concatenate(buffer_frase)
                        self._save_debug_audio(audio_sujo, "debug_original.wav")
                        
                        try:
                            audio_limpo = nr.reduce_noise(y=audio_sujo, sr=SAMPLE_RATE, stationary=True)
                            self._save_debug_audio(audio_limpo, "debug_limpo.wav")
                            self._transcrever(audio_limpo)
                        except Exception as e:
                            self.log.error(f"Erro NR: {e}")
                            self._transcrever(audio_sujo)
                        
                        buffer_frase = []
                        falando = False
                        blocos_silencio = 0

    def _transcrever(self, audio_data):
        try:
            segments, info = self.model.transcribe(audio_data, beam_size=5, language="pt")
            texto_final = " ".join([s.text for s in segments]).strip()
            
            if texto_final:
                self.log.info(f"📝 Whisper ouviu: '{texto_final}'")
                self.normalizer.process(texto_final)
            else:
                self.log.warning("⚠️ Vazio. (Ruído filtrado)")
                
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

ears = WhisperListenService()