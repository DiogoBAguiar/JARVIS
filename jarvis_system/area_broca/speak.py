import os
import threading
import queue
import asyncio
import hashlib
import pygame
import edge_tts
import pyttsx3
import json
from typing import Optional

# Core Imports
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos

# Configurações de Voz
VOICE_NAME = "pt-BR-AntonioNeural"

class NeuralSpeaker:
    def __init__(self):
        self.log = JarvisLogger("BROCA_VOICE")
        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread = None
        
        # --- CAMADAS DE MEMÓRIA DE VOZ ---
        # 1. Pasta de Áudios "Premium" (Pré-moldados com F5-TTS)
        self.static_dir = os.path.join(os.path.dirname(__file__), "static_audio")
        os.makedirs(self.static_dir, exist_ok=True)
        
        # 2. Pasta de Cache Dinâmico (Para não baixar a mesma frase 2x)
        self.cache_dir = os.path.join(os.getcwd(), "jarvis_system", "data", "voice_cache")
        os.makedirs(self.cache_dir, exist_ok=True)

        # [NOVO] Arquivo de Aprendizado (Onde anotamos o que falta)
        self.arquivo_faltantes = os.path.join(os.getcwd(), "jarvis_system", "data", "vocabulario_pendente.txt")
        self.palavras_faltantes = set()

        # 3. Mapeamento Texto -> Arquivo Fixo
        # Dica: Use chaves em minúsculo e sem pontuação para facilitar o match
        self.soundboard = {
            "sim senhor": "sim_senhor.mp3",
            "pois não": "pois_nao.mp3",
            "sistemas online": "sistemas_online.mp3",
            "processando": "processando.mp3",
            "entendido": "entendido.mp3",
            "claro": "claro.mp3",
            "desligando sistemas": "desligando.mp3",
            "acesso autorizado": "acesso_autorizado.mp3",
            "acesso negado": "acesso_negado.mp3"
        }

        # Inicializa Mixers
        try:
            pygame.mixer.init()
        except Exception as e:
            self.log.critical(f"Erro audio: {e}")

        self.engine_offline = None
        self._setup_offline_tts()
        
        # Se inscreve para receber ordens de fala
        bus.inscrever(Eventos.FALAR, self._adicionar_a_fila)

    def _setup_offline_tts(self):
        """Configura o pyttsx3 para caso a internet falhe."""
        try:
            self.engine_offline = pyttsx3.init()
            # Tenta encontrar uma voz em português no sistema
            voices = self.engine_offline.getProperty('voices')
            for voice in voices:
                if "brazil" in voice.name.lower() or "portuguese" in voice.name.lower():
                    self.engine_offline.setProperty('voice', voice.id)
                    break
        except: pass

    def _adicionar_a_fila(self, evento: Evento):
        texto = evento.dados.get("texto")
        if texto: self._queue.put(texto)

    def _normalizar_chave(self, texto: str) -> str:
        """Limpa o texto para tentar achar no soundboard (remove pontuação básica)."""
        return texto.lower().strip().replace(".", "").replace("!", "")

    def _registrar_falta(self, texto: str):
        """Anota frases curtas que não temos no banco para aprender depois."""
        # Só aprende frases curtas (1 a 4 palavras) para não poluir o banco com frases complexas demais
        if len(texto.split()) > 4: return
        
        if texto not in self.palavras_faltantes:
            self.palavras_faltantes.add(texto)
            try:
                # Garante que o diretório data existe
                os.makedirs(os.path.dirname(self.arquivo_faltantes), exist_ok=True)
                with open(self.arquivo_faltantes, "a", encoding="utf-8") as f:
                    f.write(f"{texto}\n")
                self.log.debug(f"📝 Anotado para aprender: '{texto}'")
            except Exception as e:
                self.log.warning(f"Erro ao registrar vocabulario: {e}")

    def _worker(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while not self._stop_event.is_set():
            try:
                texto_original = self._queue.get(timeout=1.0)
                texto_chave = self._normalizar_chave(texto_original)
                
                bus.publicar(Evento(Eventos.STATUS_FALA, {"status": True}))
                sucesso = False

                # ---------------------------------------------------------
                # CAMADA 1: SOUNDBOARD (Áudios de Estúdio Pré-Gravados)
                # ---------------------------------------------------------
                if texto_chave in self.soundboard:
                    arquivo_fixo = os.path.join(self.static_dir, self.soundboard[texto_chave])
                    if os.path.exists(arquivo_fixo):
                        self.log.info(f"💿 Soundboard: '{texto_chave}'")
                        self._reproduzir_audio_pygame(arquivo_fixo)
                        sucesso = True
                
                # ---------------------------------------------------------
                # CAMADA 2: CACHE DINÂMICO (Já gerou isso antes?)
                # ---------------------------------------------------------
                if not sucesso:
                    hash_md5 = hashlib.md5(texto_original.encode()).hexdigest()
                    arquivo_cache = os.path.join(self.cache_dir, f"{hash_md5}.mp3")
                    
                    if os.path.exists(arquivo_cache):
                        self.log.debug(f"⚡ Cache Hit: '{texto_original[:15]}...'")
                        self._reproduzir_audio_pygame(arquivo_cache)
                        sucesso = True
                    else:
                        # [NOVO] OPORTUNIDADE DE APRENDIZADO
                        # Se não temos cache nem soundboard, anotamos para a Fábrica F5 gerar depois
                        self._registrar_falta(texto_chave)

                        # -----------------------------------------------------
                        # CAMADA 3: GERAÇÃO ONLINE (Edge TTS)
                        # -----------------------------------------------------
                        try:
                            # Gera e SALVA no cache para a próxima vez
                            communicate = edge_tts.Communicate(texto_original, VOICE_NAME)
                            loop.run_until_complete(communicate.save(arquivo_cache))
                            
                            self._reproduzir_audio_pygame(arquivo_cache)
                            sucesso = True
                        except Exception as e:
                            self.log.warning(f"Falha online: {e}")

                # ---------------------------------------------------------
                # CAMADA 4: FALLBACK (Robótico)
                # ---------------------------------------------------------
                if not sucesso:
                    self._falar_offline(texto_original)

                bus.publicar(Evento(Eventos.STATUS_FALA, {"status": False}))
                self._queue.task_done()

            except queue.Empty: continue
            except Exception as e:
                self.log.error(f"Erro worker: {e}")
                bus.publicar(Evento(Eventos.STATUS_FALA, {"status": False}))

    def _reproduzir_audio_pygame(self, caminho: str):
        try:
            pygame.mixer.music.load(caminho)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy() and not self._stop_event.is_set():
                pygame.time.Clock().tick(10)
            pygame.mixer.music.unload()
        except Exception as e:
            self.log.error(f"Erro playback: {e}")

    def _falar_offline(self, texto):
        if self.engine_offline:
            self.engine_offline.say(texto)
            self.engine_offline.runAndWait()

    def start(self):
        # CORREÇÃO: Separar a criação do start para não perder a referência
        if not self._thread or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._worker, name="BrocaSpeaker", daemon=True)
            self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)

# Instância Global
mouth = NeuralSpeaker()