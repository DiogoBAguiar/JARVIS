import os
import asyncio
import threading
import edge_tts
import pygame
import time
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus
from jarvis_system.protocol import Eventos

log = JarvisLogger("BROCA_VOICE")

# Configuração de Voz
# Lista de vozes disponíveis: edge-tts --list-voices
VOICE = "pt-BR-AntonioNeural"  # Voz masculina natural (Online)
TEMP_AUDIO_FILE = "fala_temp.mp3"

class SpeakService:
    """
    Serviço de Síntese de Voz (TTS) Neural.
    Usa Edge-TTS (Online) com arquitetura não-bloqueante.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self.is_active = False
        
        # Inicializa mixer de áudio (headless friendly)
        try:
            pygame.mixer.init()
        except Exception as e:
            log.warning(f"Audio driver não detectado (Servidor?): {e}")

    def start(self):
        """Ativa o serviço e inscreve no barramento"""
        bus.inscrever(Eventos.FALAR, self._processar_fala)
        self.is_active = True
        log.info(f"Córtex Vocal Online. Voz: {VOICE}")

    def stop(self):
        """Encerra graciosamente"""
        self.is_active = False
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
            # Tenta limpar arquivo residual
            if os.path.exists(TEMP_AUDIO_FILE):
                os.remove(TEMP_AUDIO_FILE)
        except:
            pass
        log.info("Córtex Vocal Offline.")

    def _processar_fala(self, evento):
        """Callback acionado quando o sistema decide falar."""
        if not self.is_active: return

        texto = evento.dados.get("texto")
        if texto:
            # Dispara thread para não travar o sistema enquanto baixa o áudio
            threading.Thread(target=self._falar_sync, args=(texto,)).start()

    def _falar_sync(self, texto: str):
        """Wrapper síncrono para executar o loop assíncrono."""
        try:
            asyncio.run(self._gerar_e_tocar(texto))
        except Exception as e:
            log.error(f"Falha no subsistema de voz: {e}")
            # Fallback: Se não puder falar, loga CRITICAL para o operador ler
            log.critical(f"FALLBACK (TEXTO): {texto}")

    async def _gerar_e_tocar(self, texto: str):
        """
        1. Conecta na API da MS (Edge)
        2. Baixa o MP3
        3. Toca localmente
        """
        log.info(f"Sintetizando: '{texto}' ...")
        
        # Usa Lock para garantir que não fale uma frase em cima da outra
        with self._lock: 
            try:
                communicate = edge_tts.Communicate(texto, VOICE)
                await communicate.save(TEMP_AUDIO_FILE)
                
                if not os.path.exists(TEMP_AUDIO_FILE):
                    raise FileNotFoundError("Arquivo de áudio não gerado.")

                # Reprodução
                pygame.mixer.music.load(TEMP_AUDIO_FILE)
                pygame.mixer.music.play()
                
                # Aguarda terminar de falar (bloqueia apenas esta thread)
                while pygame.mixer.music.get_busy():
                    if not self.is_active: 
                        pygame.mixer.music.stop()
                        break
                    pygame.time.Clock().tick(10)
                
                # Libera o arquivo para poder deletar
                pygame.mixer.music.unload()

            except Exception as e:
                log.error(f"Erro ao tocar áudio: {e}")
            
            finally:
                # Limpeza crucial para evitar erro de permissão na próxima vez
                try:
                    if os.path.exists(TEMP_AUDIO_FILE):
                        os.remove(TEMP_AUDIO_FILE)
                except Exception as e:
                    log.warning(f"Não foi possível limpar temp: {e}")

# Singleton
mouth = SpeakService()