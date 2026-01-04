import os
import json
import queue
import threading
import sounddevice as sd
import vosk
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos

log = JarvisLogger("BROCA_JUDGE")

# Configurações
SAMPLE_RATE = 16000
BLOCK_SIZE = 8000
CHANNELS = 1

# Caminhos Relativos
AREA_BROCA_DIR = os.path.dirname(os.path.abspath(__file__))
PATH_PT = os.path.join(AREA_BROCA_DIR, "model_pt")
PATH_EN = os.path.join(AREA_BROCA_DIR, "model_en")

class DualListenService:
    def __init__(self):
        self._queue = queue.Queue()
        self._running = False
        self._thread = None
        self.rec_pt = None
        self.rec_en = None
        
        # --- DICIONÁRIO DE ENTIDADES FORTES (INGLÊS) ---
        # Se o modelo EN ouvir isso, ele ganha prioridade total sobre o objeto da frase
        self.apps_priority = {
            "spotify": "spotify",
            "whatsapp": "whatsapp",
            "chrome": "chrome",
            "firefox": "firefox",
            "league of legends": "league of legends",
            "photoshop": "photoshop",
            "visual studio": "code",
            "code": "code",
            "discord": "discord",
            "steam": "steam"
        }

        self._load_models()

    def _load_models(self):
        log.info("Inicializando Validação Cruzada (PT/EN)...")
        vosk.SetLogLevel(-1) # Silencia logs internos do Vosk

        if os.path.exists(PATH_PT):
            try:
                self.rec_pt = vosk.KaldiRecognizer(vosk.Model(PATH_PT), SAMPLE_RATE)
            except Exception as e:
                log.critical(f"Erro PT: {e}")
        
        if os.path.exists(PATH_EN):
            try:
                self.rec_en = vosk.KaldiRecognizer(vosk.Model(PATH_EN), SAMPLE_RATE)
            except Exception as e:
                log.critical(f"Erro EN: {e}")

    def _callback(self, indata, frames, time, status):
        self._queue.put(bytes(indata))

    def _listen_loop(self):
        if not self.rec_pt and not self.rec_en: return
        log.info(f"Juiz Auditivo: Monitorando Fluxos...")
        
        try:
            with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE, device=None,
                                   dtype='int16', channels=CHANNELS, callback=self._callback):
                
                while self._running:
                    try:
                        data = self._queue.get(timeout=1.0)
                    except queue.Empty:
                        continue

                    # Captura resultados
                    raw_pt = ""
                    raw_en = ""
                    
                    if self.rec_pt and self.rec_pt.AcceptWaveform(data):
                        raw_pt = json.loads(self.rec_pt.Result()).get("text", "")
                    
                    if self.rec_en and self.rec_en.AcceptWaveform(data):
                        raw_en = json.loads(self.rec_en.Result()).get("text", "")

                    if raw_pt or raw_en:
                        self._reconstruir_intencao(raw_pt, raw_en)

        except Exception as e:
            log.critical(f"Erro loop: {e}")
            self._running = False

    def _reconstruir_intencao(self, pt: str, en: str):
        """
        O GRANDE CÉREBRO AUDITIVO:
        Em vez de corrigir palavras, ele monta o quebra-cabeça.
        """
        if not pt and not en: return

        pt_lower = pt.lower()
        en_lower = en.lower()
        
        # Peças do Quebra-Cabeça
        peca_sujeito = None   # Ex: Jarvis
        peca_acao = None      # Ex: Abrir
        peca_objeto = None    # Ex: Spotify

        # 1. QUEM? (Wake Word)
        # Inglês tem prioridade máxima no nome "Jarvis"
        if "jarvis" in en_lower:
            peca_sujeito = "jarvis"
        # Fallback para PT se EN falhar
        elif any(x in pt_lower for x in ["já vi", "já vos", "chaves", "james", "jacques", "jardim"]):
            peca_sujeito = "jarvis"

        # 2. AÇÃO? (Verbos em Português)
        # O modelo PT é mestre em verbos
        verbos_pt = ["abrir", "fechar", "tocar", "pesquisar", "busca", "apagar", "memorize", "lembre"]
        for v in verbos_pt:
            if v in pt_lower:
                peca_acao = v
                break # Pega o primeiro verbo que achar

        # 3. O QUÊ? (Entidades em Inglês)
        # O modelo EN é mestre em nomes de Apps
        for app_en, nome_real in self.apps_priority.items():
            if app_en in en_lower:
                peca_objeto = nome_real
                break

        # --- FUSÃO NUCLEAR (A Lógica que você pediu) ---
        
        # Cenário Ideal: Temos as 3 peças (Jarvis + Abrir + Spotify)
        if peca_sujeito == "jarvis" and peca_acao == "abrir" and peca_objeto:
            frase_reconstruida = f"jarvis abrir {peca_objeto}"
            log.info(f"🧩 RECONSTRUÇÃO PERFEITA: '{frase_reconstruida}' (Ignorando lixo do PT)")
            bus.publicar(Evento(Eventos.FALA_RECONHECIDA, {"texto": frase_reconstruida}))
            return

        # Cenário Parcial: Temos Jarvis + Objeto (Ex: "Jarvis Spotify")
        # Assumimos "abrir" se não tiver verbo, ou passamos direto
        if peca_sujeito == "jarvis" and peca_objeto and not peca_acao:
             # Opcional: inferir 'abrir' ou mandar só o nome
             frase_reconstruida = f"jarvis abrir {peca_objeto}"
             log.info(f"🧩 RECONSTRUÇÃO (Inferida): '{frase_reconstruida}'")
             bus.publicar(Evento(Eventos.FALA_RECONHECIDA, {"texto": frase_reconstruida}))
             return

        # --- FALLBACK (Se não conseguiu reconstruir tudo) ---
        # Se não detectamos um "App em Inglês", confiamos no PT original,
        # mas garantimos que a Wake Word esteja certa.
        
        texto_base = pt if pt else en
        
        if peca_sujeito == "jarvis":
             # Força 'jarvis' no início da frase PT original
             palavras = texto_base.split()
             if palavras:
                 palavras[0] = "jarvis"
                 texto_final = " ".join(palavras)
             else:
                 texto_final = "jarvis"
                 
             log.info(f"👂 Ouvido (Corrigido): '{texto_final}'")
             bus.publicar(Evento(Eventos.FALA_RECONHECIDA, {"texto": texto_final}))
             
        elif texto_base.strip():
             # Só conversa aleatória
             log.info(f"👂 Ouvido (Original): '{texto_base}'")
             bus.publicar(Evento(Eventos.FALA_RECONHECIDA, {"texto": texto_base}))

    def start(self):
        if self._running: return
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, name="JudgeThread", daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread: self._thread.join(timeout=2.0)

ears = DualListenService()