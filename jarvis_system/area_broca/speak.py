import os
import threading
import queue
import asyncio
import pygame
import edge_tts
import pyttsx3  # <--- NOVA DEPENDÊNCIA (pip install pyttsx3)
from typing import Optional

# Core Imports
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos

# Configurações de Voz Online (Edge)
VOICE_NAME = "pt-BR-AntonioNeural"
RATE = "+0%"
VOLUME = "+0%"

class NeuralSpeaker:
    def __init__(self):
        self.log = JarvisLogger("BROCA_VOICE")
        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread = None
        
        # 1. Inicializa Mixer Online (Pygame)
        try:
            pygame.mixer.init()
            self.log.info(f"🔊 Córtex Vocal Online Ativo ({VOICE_NAME})")
        except Exception as e:
            self.log.critical(f"Erro no mixer de áudio: {e}")

        # 2. Inicializa Motor Offline (Fallback)
        self.engine_offline = None
        self._setup_offline_tts()

        # Se inscreve para receber ordens de fala
        bus.inscrever(Eventos.FALAR, self._adicionar_a_fila)

    def _setup_offline_tts(self):
        """Configura o pyttsx3 para caso a internet falhe."""
        try:
            self.engine_offline = pyttsx3.init()
            voices = self.engine_offline.getProperty('voices')
            # Tenta achar uma voz em português
            for voice in voices:
                if "brazil" in voice.name.lower() or "portuguese" in voice.name.lower():
                    self.engine_offline.setProperty('voice', voice.id)
                    break
            self.log.info("🛡️ Sistema de Voz de Backup (Offline) armado.")
        except Exception as e:
            self.log.error(f"Falha ao iniciar motor offline: {e}")

    def _adicionar_a_fila(self, evento: Evento):
        """Recebe o texto do Cérebro e coloca na fila."""
        texto = evento.dados.get("texto")
        if texto:
            self._queue.put(texto)

    def _worker(self):
        """Loop principal da Thread de Fala."""
        # Cria um loop async para o Edge TTS
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while not self._stop_event.is_set():
            try:
                # 1. Espera por texto
                texto = self._queue.get(timeout=1.0)
                
                # 2. Notifica o sistema: "VOU FALAR"
                bus.publicar(Evento(Eventos.STATUS_FALA, {"status": True}))
                
                # 3. TENTATIVA 1: Voz Neural (Online)
                sucesso_online = False
                try:
                    arquivo_temp = self._gerar_audio_edge(loop, texto)
                    if arquivo_temp:
                        self._reproduzir_audio_pygame(arquivo_temp)
                        self._limpar_temp(arquivo_temp)
                        sucesso_online = True
                except Exception as e:
                    self.log.warning(f"Falha na voz neural ({e}). Tentando offline...")
                
                # 4. TENTATIVA 2: Voz Robótica (Offline) - Se a online falhou
                if not sucesso_online:
                    self._falar_offline(texto)

                # 5. Notifica o sistema: "TERMINEI"
                bus.publicar(Evento(Eventos.STATUS_FALA, {"status": False}))
                self._queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                self.log.error(f"Erro crítico no loop vocal: {e}")
                bus.publicar(Evento(Eventos.STATUS_FALA, {"status": False}))

    def _gerar_audio_edge(self, loop, texto: str) -> Optional[str]:
        """Gera MP3 usando Edge-TTS."""
        arquivo_saida = os.path.join(os.getcwd(), "temp_speech.mp3")
        
        # Gera o áudio (pode lançar erro 403 se bloqueado)
        communicate = edge_tts.Communicate(texto, VOICE_NAME, rate=RATE, volume=VOLUME)
        loop.run_until_complete(communicate.save(arquivo_saida))
        
        return arquivo_saida

    def _reproduzir_audio_pygame(self, caminho_arquivo: str):
        """Toca o arquivo gerado."""
        pygame.mixer.music.load(caminho_arquivo)
        pygame.mixer.music.play()
        
        print(f"🗣️  JARVIS (Cloud): '{caminho_arquivo}'") 
        
        while pygame.mixer.music.get_busy() and not self._stop_event.is_set():
            pygame.time.Clock().tick(10)

    def _falar_offline(self, texto: str):
        """Usa o motor do sistema operacional (SAPI5/NSSS/Espeak)."""
        if self.engine_offline:
            print(f"🗣️  JARVIS (Offline): '{texto}'")
            try:
                self.engine_offline.say(texto)
                self.engine_offline.runAndWait()
            except Exception as e:
                self.log.error(f"Erro na voz offline: {e}")

    def _limpar_temp(self, caminho: str):
        try:
            pygame.mixer.music.unload()
            if os.path.exists(caminho):
                os.remove(caminho)
        except: pass

    def start(self):
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