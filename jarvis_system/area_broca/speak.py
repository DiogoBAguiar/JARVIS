import os
import asyncio
import threading
import edge_tts
import pygame
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus
from jarvis_system.protocol import Eventos

log = JarvisLogger("BROCA_VOICE")

# Configuração de Voz
# Lista de vozes: edge-tts --list-voices
VOICE = "pt-BR-AntonioNeural"  # Voz masculina natural
TEMP_AUDIO_FILE = "fala_temp.mp3"

class SpeakService:
    """
    Serviço de Síntese de Voz (TTS).
    Prioriza voz neural (Online) com arquitetura não-bloqueante.
    """
    def __init__(self):
        self._lock = threading.Lock()
        
        # Inicializa mixer de áudio (headless friendly)
        try:
            pygame.mixer.init()
        except Exception as e:
            log.warning(f"Audio driver não detectado (Servidor?): {e}")

        # Inscreve-se para ouvir ordens de fala do Cérebro
        bus.inscrever(Eventos.FALAR, self._processar_fala)

    def _processar_fala(self, evento):
        """Callback acionado quando o sistema decide falar."""
        texto = evento.dados.get("texto")
        if texto:
            # Dispara thread para não travar o sistema enquanto baixa o áudio
            threading.Thread(target=self._falar_sync, args=(texto,)).start()

    def _falar_sync(self, texto: str):
        """Wrapper síncrono para executar o loop assíncrono."""
        try:
            asyncio.run(self._gerar_e_tocar(texto))
        except Exception as e:
            log.error("Falha no subsistema de voz", error=str(e))
            # Fallback: Se não puder falar, loga CRITICAL para o operador ler
            log.critical(f"FALLBACK (TEXTO): {texto}")

    async def _gerar_e_tocar(self, texto: str):
        """
        1. Conecta na API da MS (Edge)
        2. Baixa o MP3
        3. Toca localmente
        """
        log.info(f"Sintetizando: '{texto}' ...")
        
        with self._lock:  # Garante que não fale duas coisas ao mesmo tempo
            communicate = edge_tts.Communicate(texto, VOICE)
            await communicate.save(TEMP_AUDIO_FILE)
            
            if not os.path.exists(TEMP_AUDIO_FILE):
                raise FileNotFoundError("Arquivo de áudio não gerado.")

            # Reprodução
            pygame.mixer.music.load(TEMP_AUDIO_FILE)
            pygame.mixer.music.play()
            
            # Aguarda terminar de falar (bloqueia apenas esta thread, não o sistema)
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
            # Limpeza
            pygame.mixer.music.unload()
            # Opcional: os.remove(TEMP_AUDIO_FILE)

# Singleton
mouth = SpeakService()