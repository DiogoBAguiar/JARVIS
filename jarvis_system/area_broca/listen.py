import os
import json
import queue
import threading
import sounddevice as sd
import vosk
from typing import Optional, List

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
        log.info("Inicializando Validação Cruzada (PT <-> EN)...")
        if os.path.exists(PATH_PT):
            self.rec_pt = vosk.KaldiRecognizer(vosk.Model(PATH_PT), SAMPLE_RATE)
        if os.path.exists(PATH_EN):
            self.rec_en = vosk.KaldiRecognizer(vosk.Model(PATH_EN), SAMPLE_RATE)

    def _callback(self, indata, frames, time, status):
        self._queue.put(bytes(indata))

    def _listen_loop(self):
        log.info("Monitoramento Ativo. Juiz Tolerante pronto.")
        
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
        
        # 1. Atualização baseada nos seus logs recentes
        confusoes_pt = [
            "jardins", "jardim", "já vos", "chaves", "james", 
            "tardes", "aves", "jovens", "já", "já disse"
        ]
        
        validadores_en = ["jarvis", "service", "harvest", "java", "davis", "jobs", "chavis"]

        vencedor = pt # Default

        # CASO A: EN ouviu "Jarvis" explicitamente -> Vitória Suprema
        if "jarvis" in en_lower:
            vencedor = en

        # CASO B: PT ouviu uma confusão conhecida ("Chaves", "Jovens")
        elif any(erro in pt_lower for erro in confusoes_pt):
            
            # Sub-caso B1: O EN confirma ("Harvest")
            en_confirma = any(validador in en_lower for validador in validadores_en)
            
            # Sub-caso B2: O EN está MUDO (Vazio)
            # Se o PT tem certeza que ouviu "Chaves" e o EN não ouviu nada, 
            # damos o benefício da dúvida e assumimos que é Wake Word.
            en_mudo = (en_lower.strip() == "")

            if en_confirma:
                log.info(f"[JUIZ] Confirmado por EN: '{en}' -> WAKE WORD")
                vencedor = "jarvis" # Força wake word limpa
                
            elif en_mudo:
                log.info(f"[JUIZ] EN Mudo. PT '{pt}' é suspeito forte -> WAKE WORD (Benefício da Dúvida)")
                vencedor = "jarvis" # Força wake word limpa
                
            else:
                # Se EN ouviu algo diferente (ex: "Banana"), aí sim vetamos
                log.info(f"[JUIZ] Vetado por EN: '{en}' -> Mantém '{pt}'")
                vencedor = pt

        # Publica
        if vencedor == "jarvis":
             # Se decidimos que é wake word, mandamos limpo
             bus.publicar(Evento(Eventos.FALA_RECONHECIDA, {"texto": "jarvis"}))
        else:
             bus.publicar(Evento(Eventos.FALA_RECONHECIDA, {"texto": vencedor}))
             log.info(f"Ouvido Final: '{vencedor}'")

    def start(self):
        if self._running: return
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, name="JudgeThread", daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread: self._thread.join()

ears = DualListenService()