import os
import json
import queue
import threading
import sounddevice as sd
import vosk
from typing import Optional

from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos

log = JarvisLogger("BROCA_JUDGE")

# Configurações
SAMPLE_RATE = 16000
BLOCK_SIZE = 8000
CHANNELS = 1

PATH_PT = "jarvis_system/area_broca/model_pt"
PATH_EN = "jarvis_system/area_broca/model_en"

class DualListenService:
    def __init__(self):
        self._queue = queue.Queue()
        self._running = False
        self._thread = None
        self.rec_pt = None
        self.rec_en = None
        self._load_models()

    def _load_models(self):
        log.info("Inicializando Validação Cruzada...")
        if os.path.exists(PATH_PT):
            self.rec_pt = vosk.KaldiRecognizer(vosk.Model(PATH_PT), SAMPLE_RATE)
        if os.path.exists(PATH_EN):
            self.rec_en = vosk.KaldiRecognizer(vosk.Model(PATH_EN), SAMPLE_RATE)

    def _callback(self, indata, frames, time, status):
        self._queue.put(bytes(indata))

    def _listen_loop(self):
        log.info("Juiz Auditivo: Pronto.")
        try:
            with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE, device=None,
                                   dtype='int16', channels=CHANNELS, callback=self._callback):
                while self._running:
                    try:
                        data = self._queue.get(timeout=1.0)
                    except queue.Empty:
                        continue

                    text_pt = ""
                    text_en = ""
                    
                    if self.rec_pt and self.rec_pt.AcceptWaveform(data):
                        text_pt = json.loads(self.rec_pt.Result()).get("text", "")
                    
                    if self.rec_en and self.rec_en.AcceptWaveform(data):
                        text_en = json.loads(self.rec_en.Result()).get("text", "")

                    if text_pt or text_en:
                        self._julgar_e_publicar(text_pt, text_en)

        except Exception as e:
            log.error("Erro auditivo", error=str(e))
            self._running = False

    def _julgar_e_publicar(self, pt: str, en: str):
        if not pt and not en: return

        pt_lower = pt.lower()
        en_lower = en.lower()
        
        confusoes_pt = [
            "jardins", "jardim", "já vos", "chaves", "james", 
            "tardes", "aves", "jovens", "já", "já disse"
        ]
        
        validadores_en = ["jarvis", "service", "harvest", "java", "davis", "jobs", "chavis"]

        # Variável para armazenar o texto final corrigido
        texto_final = pt # Começamos assumindo que o PT está certo

        eh_wake_word = False

        # CASO A: EN ouviu "Jarvis" explicitamente
        if "jarvis" in en_lower:
            eh_wake_word = True
            # Se o PT ouviu algo diferente no começo, vamos reconstruir usando o PT como base
            # mas forçando "jarvis" no início
            texto_final = self._forcar_wake_word(pt)

        # CASO B: PT ouviu uma confusão conhecida
        elif any(erro in pt_lower for erro in confusoes_pt):
            
            en_confirma = any(validador in en_lower for validador in validadores_en)
            en_mudo = (en_lower.strip() == "")

            if en_confirma or en_mudo:
                log.info(f"[JUIZ] Correção Ativada (PT='{pt}' | EN='{en}')")
                eh_wake_word = True
                texto_final = self._forcar_wake_word(pt)
            else:
                log.info(f"[JUIZ] Vetado (PT='{pt}' | EN='{en}')")

        # Publica
        if eh_wake_word:
             log.info(f"Ouvido Final (Corrigido): '{texto_final}'")
             bus.publicar(Evento(Eventos.FALA_RECONHECIDA, {"texto": texto_final}))
        else:
             # Se não for wake word, manda o que veio (provavelmente comando puro ou lixo)
             # Mas só mandamos se não for vazio
             if texto_final.strip():
                log.info(f"Ouvido Final (Original): '{texto_final}'")
                bus.publicar(Evento(Eventos.FALA_RECONHECIDA, {"texto": texto_final}))

    def _forcar_wake_word(self, texto_original: str) -> str:
        """
        Pega a frase original (ex: 'James abre a porta') e troca a primeira palavra por 'jarvis'.
        """
        palavras = texto_original.split()
        if not palavras:
            return "jarvis"
        
        # Troca a primeira palavra (o erro) pela correta
        palavras[0] = "jarvis"
        return " ".join(palavras)

    def start(self):
        if self._running: return
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, name="JudgeThread", daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread: self._thread.join()

ears = DualListenService()