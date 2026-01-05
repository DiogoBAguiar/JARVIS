import os
import json
import queue
import threading
import time
import re
from typing import Optional, Dict, List
import sounddevice as sd
import vosk

# Core Imports
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos

# --- INTEGRAÇÃO COM MEMÓRIA DE APRENDIZADO ---
try:
    from jarvis_system.hipocampo.reflexos import reflexos
except ImportError:
    class ReflexosMock:
        def corrigir(self, t): return t
    reflexos = ReflexosMock()

# --- CONFIGURAÇÃO ---
SAMPLE_RATE = 16000
BLOCK_SIZE = 4000
CHANNELS = 1
# Aumentado para 3s: Dá tempo de falar "Jarvis"..... "Abrir Spotify"
SYNC_WINDOW = 3.0 

# --- CARREGAMENTO DE DADOS EXTERNOS (JSON) ---
def load_speech_config():
    """Carrega as listas de palavras do arquivo JSON externo."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(base_dir, "data", "speech_config.json")
    
    defaults = {
        "wake_words": ["jarvis"],
        "confirmation_words": ["sim", "não"],
        "known_apps": ["chrome"],
        "phonetic_map": {}
    }

    if not os.path.exists(config_path):
        return defaults

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Erro ao ler speech_config.json: {e}")
        return defaults

# Carrega configurações
CONFIG = load_speech_config()
CONFIRMATION_WORDS = CONFIG.get("confirmation_words", [])
PHONETIC_MAP = CONFIG.get("phonetic_map", {})
KNOWN_APPS = CONFIG.get("known_apps", [])
WAKE_WORDS = CONFIG.get("wake_words", [])

class IntentionNormalizer:
    def __init__(self, logger: JarvisLogger):
        self.log = logger
        self._text_buffer = []
        self._last_input_time = 0.0

    def process(self, raw_pt: str, raw_en: str):
        now = time.time()
        
        # Limpa o buffer se passou muito tempo em silêncio
        if (now - self._last_input_time) > SYNC_WINDOW:
            if self._text_buffer:
                self.log.debug("🧹 Buffer limpo por inatividade.")
            self._text_buffer = []

        clean_pt = self._apply_phonetic_fix(raw_pt)
        clean_en = self._apply_phonetic_fix(raw_en)

        if not clean_pt and not clean_en: return

        self._last_input_time = now
        
        # --- ESTRATÉGIA DE FUSÃO HÍBRIDA (PT + EN) ---
        # Priorizamos o PT, pois é a língua nativa do usuário.
        # Usamos o EN apenas para capturar 'Jarvis' ou nomes de Apps que o PT errou.
        merged_text = clean_pt
        
        # 1. Recuperação de Wake Word (Se o inglês ouviu Jarvis e o PT não)
        if "jarvis" in clean_en and "jarvis" not in merged_text:
            merged_text = f"jarvis {merged_text}"
        
        # 2. Recuperação de Apps (Se o inglês ouviu 'Spotify' e o PT ouviu 'Esporte')
        pt_has_app = any(app in merged_text for app in KNOWN_APPS)
        if not pt_has_app:
            for app in KNOWN_APPS:
                if app in clean_en and app not in merged_text:
                    merged_text += f" {app}"
                    break 

        self._text_buffer.append(merged_text.strip())

        full_phrase = " ".join(self._text_buffer).strip()
        full_phrase = self._remove_duplicates(full_phrase)

        if self._is_actionable(full_phrase):
            self.log.info(f"🧩 INTENÇÃO CANÔNICA: '{full_phrase}'")
            bus.publicar(Evento(Eventos.FALA_RECONHECIDA, {"texto": full_phrase}))
            self._text_buffer = []

    def _apply_phonetic_fix(self, text: str) -> str:
        if not text: return ""
        text = text.lower().strip()
        text = reflexos.corrigir(text)

        words = text.split()
        fixed_words = []
        for w in words:
            candidate = PHONETIC_MAP.get(w, w)
            fixed_words.append(candidate)
        return " ".join(fixed_words)

    def _remove_duplicates(self, text: str) -> str:
        words = text.split()
        if not words: return ""
        result = [words[0]]
        for w in words[1:]:
            if w != result[-1]: 
                result.append(w)
        return " ".join(result)

    def _is_actionable(self, text: str) -> bool:
        text_clean = text.lower().strip()
        if "jarvis" in text_clean: return True
        # Verifica palavra exata para evitar falso positivo em frases longas
        if text_clean in CONFIRMATION_WORDS: return True
        return False


class DualListenService:
    def __init__(self):
        self.log = JarvisLogger("BROCA_EARS")
        self.normalizer = IntentionNormalizer(self.log)
        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread = None
        
        self._is_jarvis_speaking = False
        bus.inscrever(Eventos.STATUS_FALA, self._on_speech_status)
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.path_pt = os.path.join(base_dir, "model_pt")
        self.path_en = os.path.join(base_dir, "model_en")
        
        self.rec_pt = None
        self.rec_en = None
        self._load_models()

    def _load_models(self):
        vosk.SetLogLevel(-1)
        if os.path.exists(self.path_pt):
            try:
                self.rec_pt = vosk.KaldiRecognizer(vosk.Model(self.path_pt), SAMPLE_RATE)
                self.log.info("✅ Modelo PT (Generalista) carregado.")
            except Exception: pass
        
        if os.path.exists(self.path_en):
            try:
                # --- MUDANÇA CRÍTICA: REMOVIDO 'VOCAB_EN' ---
                # Agora o modelo EN ouve tudo, não limitamos mais palavras.
                self.rec_en = vosk.KaldiRecognizer(vosk.Model(self.path_en), SAMPLE_RATE)
                self.log.info("✅ Modelo EN (Unrestricted) carregado.")
            except Exception: pass

    def _on_speech_status(self, evento: Evento):
        self._is_jarvis_speaking = evento.dados.get("status", False)
        if self._is_jarvis_speaking:
            with self._queue.mutex:
                self._queue.queue.clear()

    def _audio_callback(self, indata, frames, time, status):
        self._queue.put(bytes(indata))

    def _check_microphones(self):
        print("\n--- MICROFONES DETECTADOS ---")
        try:
            default_input = sd.query_devices(kind='input')
            print(f"Padrão: {default_input['name']}")
        except: pass
        print("-----------------------------\n")

    def _worker(self):
        self._check_microphones()
        self.log.info(f"👂 Pipeline V2.7 (Vocabulário Livre) Ativo.")
        try:
            with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE, device=None,
                                   dtype='int16', channels=CHANNELS, callback=self._audio_callback):
                
                while not self._stop_event.is_set():
                    try:
                        data = self._queue.get(timeout=0.5)
                    except queue.Empty: continue

                    if self._is_jarvis_speaking:
                        continue 

                    raw_pt = ""
                    raw_en = ""

                    if self.rec_pt and self.rec_pt.AcceptWaveform(data):
                        raw_pt = json.loads(self.rec_pt.Result()).get("text", "")
                    
                    if self.rec_en and self.rec_en.AcceptWaveform(data):
                        raw_en = json.loads(self.rec_en.Result()).get("text", "")

                    if raw_pt: self.log.info(f"🎤 RAW PT: '{raw_pt}'")
                    if raw_en: self.log.info(f"🎤 RAW EN: '{raw_en}'")

                    if raw_pt or raw_en:
                        self.normalizer.process(raw_pt, raw_en)

        except Exception as e:
            self.log.critical(f"Erro Audio Loop: {e}")

    def start(self):
        if not self._thread or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._worker, name="BrocaListener", daemon=True)
            self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)

ears = DualListenService()