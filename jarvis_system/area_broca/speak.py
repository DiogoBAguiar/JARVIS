import os
import threading
import queue
import asyncio
import pygame
import edge_tts
from typing import Optional

# Core Imports
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos

# Configurações de Voz
VOICE_NAME = "pt-BR-AntonioNeural"  # Opções: pt-BR-FranciscaNeural, pt-BR-ThalitaNeural
RATE = "+0%"
VOLUME = "+0%"

class NeuralSpeaker:
    def __init__(self):
        self.log = JarvisLogger("BROCA_VOICE")
        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread = None
        
        # Inicializa Mixer do Pygame (para reprodução fluida)
        try:
            pygame.mixer.init()
            self.log.info(f"🔊 Córtex Vocal Ativo ({VOICE_NAME})")
        except Exception as e:
            self.log.critical(f"Erro no subsistema de áudio: {e}")

        # Se inscreve para receber ordens de fala
        bus.inscrever(Eventos.FALAR, self._adicionar_a_fila)

    def _adicionar_a_fila(self, evento: Evento):
        """Recebe o texto do Cérebro e coloca na fila de processamento."""
        texto = evento.dados.get("texto")
        if texto:
            self._queue.put(texto)

    def _worker(self):
        """Loop principal da Thread de Fala."""
        # Cria um loop de eventos Asyncio para esta thread específica
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while not self._stop_event.is_set():
            try:
                # 1. Espera por texto (bloqueia a thread, não o sistema)
                texto = self._queue.get(timeout=1.0)
                
                # 2. Notifica o sistema: "VOU FALAR" (Ouvido fica surdo agora)
                bus.publicar(Evento(Eventos.STATUS_FALA, {"status": True}))
                
                # 3. Gera e Reproduz
                arquivo_temp = self._gerar_audio(loop, texto)
                if arquivo_temp:
                    self._reproduzir_audio(arquivo_temp)
                    self._limpar_temp(arquivo_temp)

                # 4. Notifica o sistema: "TERMINEI" (Ouvido volta a escutar)
                bus.publicar(Evento(Eventos.STATUS_FALA, {"status": False}))
                
                self._queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                self.log.error(f"Erro no loop vocal: {e}")
                # Garante que o ouvido volte a funcionar mesmo se der erro
                bus.publicar(Evento(Eventos.STATUS_FALA, {"status": False}))

    def _gerar_audio(self, loop, texto: str) -> Optional[str]:
        """Gera MP3 usando Edge-TTS (Microsoft Azure Gratuito)."""
        arquivo_saida = os.path.join(os.getcwd(), "temp_speech.mp3")
        
        try:
            communicate = edge_tts.Communicate(texto, VOICE_NAME, rate=RATE, volume=VOLUME)
            # Roda a corrotina async dentro da thread síncrona
            loop.run_until_complete(communicate.save(arquivo_saida))
            return arquivo_saida
        except Exception as e:
            self.log.error(f"Erro na síntese TTS: {e}")
            return None

    def _reproduzir_audio(self, caminho_arquivo: str):
        """Toca o áudio bloqueando APENAS a thread de fala."""
        try:
            # Carrega e Toca
            pygame.mixer.music.load(caminho_arquivo)
            pygame.mixer.music.play()
            
            # Barra de progresso visual no terminal
            print(f"🗣️  JARVIS: '{caminho_arquivo}'") # Apenas debug, pode remover
            
            # Loop de espera (Busy Wait eficiente) enquanto toca
            while pygame.mixer.music.get_busy() and not self._stop_event.is_set():
                pygame.time.Clock().tick(10) # Checa a cada 100ms
                
        except Exception as e:
            self.log.error(f"Erro no player: {e}")

    def _limpar_temp(self, caminho: str):
        try:
            pygame.mixer.music.unload() # Libera o arquivo
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

# Instância Singleton
mouth = NeuralSpeaker()