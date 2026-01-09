import os
import json
import queue
import threading
import time
import re
import numpy as np
import sounddevice as sd
# import noisereduce as nr  <-- Desabilitado para reduzir latência visual
from faster_whisper import WhisperModel

# Core Imports
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos

# --- INTEGRAÇÃO COM MEMÓRIA ---
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
# Ajuste fino: Se a barra ficar cheia o tempo todo, diminua o GANHO para 5.0
LIMIAR_SILENCIO = 0.005 
GANHO_MIC = 10.0
BLOCOS_PAUSA_FIM = 8 

def load_speech_config():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(base_dir, "data", "speech_config.json")
    defaults = {"wake_words": ["jarvis"], "known_apps": ["spotify", "chrome"], "phonetic_map": {}}
    if not os.path.exists(config_path): return defaults
    try:
        with open(config_path, 'r', encoding='utf-8') as f: return json.load(f)
    except: return defaults

CONFIG = load_speech_config()
PHONETIC_MAP = CONFIG.get("phonetic_map", {})
WAKE_WORDS = CONFIG.get("wake_words", [])

# Prompt para enviesar o modelo e melhorar precisão
PALAVRAS_CHAVE = ", ".join(WAKE_WORDS + CONFIG.get("known_apps", []) + ["Tocar", "Pausar"])
PROMPT_INICIAL = f"Contexto: Assistente. Vocabulário: {PALAVRAS_CHAVE}."

class IntentionNormalizer:
    def __init__(self, logger: JarvisLogger):
        self.log = logger
        self.hallucinations = [
            "legendas pela comunidade", "amara.org", "legendado por", 
            "subtitles by", "todos os direitos reservados", "transcrição",
            "mbc", "auxiliary", "copyright"
        ]

    def process(self, text: str):
        if not text: return
        
        # 1. Filtro de Alucinação
        text_lower = text.lower()
        for h in self.hallucinations:
            if h in text_lower: return

        # 2. Correção Fonética
        clean_text = self._apply_phonetic_fix(text)
        
        # 3. Envio (Limpa a linha da barra de volume antes de logar)
        print("\r" + " " * 80 + "\r", end="") 
        self.log.info(f"🧩 INTENÇÃO: '{clean_text}'")
        bus.publicar(Evento(Eventos.FALA_RECONHECIDA, {"texto": clean_text}))

    def _apply_phonetic_fix(self, text: str) -> str:
        text = text.lower().strip()
        text = text.replace('.', '').replace(',', '').replace('?', '').replace('!', '')
        text = reflexos.corrigir(text)
        
        sorted_map = sorted(PHONETIC_MAP.items(), key=lambda x: len(x[0]), reverse=True)
        for erro, correcao in sorted_map:
            if erro in text:
                pattern = r'(?<!\w)' + re.escape(erro) + r'(?!\w)'
                text = re.sub(pattern, correcao, text, flags=re.IGNORECASE)
        return text

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
            self.log.info("✅ Whisper Pronto (VAD ON).")
        except Exception as e:
            self.log.critical(f"Falha Whisper: {e}")

    def _on_speech_status(self, evento: Evento):
        status_anterior = self._is_jarvis_speaking
        self._is_jarvis_speaking = evento.dados.get("status", False)
        
        # Feedback Visual de Mudança de Estado
        if self._is_jarvis_speaking and not status_anterior:
            print("\r" + " " * 80 + "\r", end="")
            print("🛑 JARVIS FALANDO (Microfone Pausado)...")
        elif not self._is_jarvis_speaking and status_anterior:
            print("👂 Ouvido Reativado.")

        if self._is_jarvis_speaking:
            with self._queue.mutex:
                self._queue.queue.clear()

    def _audio_callback(self, indata, frames, time, status):
        self._queue.put(indata.copy())

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

                # Processamento
                chunk_float = ((chunk_int16.astype(np.float32) / 32768.0) * GANHO_MIC).flatten()
                volume = np.linalg.norm(chunk_float) / np.sqrt(len(chunk_float))
                
                # --- VISUALIZAÇÃO SEMPRE ATIVA ---
                # Agora mostramos a barra independente do if, mas mudamos a cor/estilo
                bar_len = int(min(volume, 1.0) * 30)
                bar = "█" * bar_len
                espaco = " " * (30 - bar_len)
                
                # Se estiver gravando (acima do limiar), mostramos diferente
                estado = "🔴 GRAVANDO" if falando else "💤 AGUARDANDO"
                if volume > LIMIAR_SILENCIO:
                    estado = "🟢 DETECTADO"
                
                # Print dinâmico que não polui log
                print(f"\r🎤 {volume:.3f} |{bar}{espaco}| {estado}", end="", flush=True)

                # Lógica de Captura
                if volume > LIMIAR_SILENCIO:
                    if not falando: falando = True
                    blocos_silencio = 0
                    buffer_frase.append(chunk_float)
                
                elif falando:
                    buffer_frase.append(chunk_float)
                    blocos_silencio += 1
                    
                    if blocos_silencio > BLOCOS_PAUSA_FIM:
                        # Limpa a linha para o log aparecer bonito
                        print("\r" + " " * 80 + "\r", end="")
                        self.log.info("⏳ Processando áudio...")
                        
                        audio_final = np.concatenate(buffer_frase)
                        self._transcrever(audio_final)
                        
                        buffer_frase = []
                        falando = False
                        blocos_silencio = 0

    def _transcrever(self, audio_data):
        try:
            segments, info = self.model.transcribe(
                audio_data, beam_size=5, language="pt",
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
                initial_prompt=PROMPT_INICIAL,
                condition_on_previous_text=False
            )
            
            texto_final = " ".join([s.text for s in segments]).strip()
            
            if texto_final:
                # Limpa linha de novo por garantia
                print("\r" + " " * 80 + "\r", end="")
                self.log.info(f"📝 Whisper ouviu: '{texto_final}'")
                self.normalizer.process(texto_final)
            else:
                # print("\r⚠️ Ruído ignorado.", end="") # Opcional
                pass
                
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