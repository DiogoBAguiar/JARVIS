# jarvis_system/area_broca/listen/audioDriver.py
import sounddevice as sd
import logging

class AudioDriver:
    def __init__(self, sample_rate, block_size, channels):
        self.logger = logging.getLogger("BROCA_DRIVER")
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.channels = channels
        self.stream = None

    def start_stream(self, callback_function):
        """Inicia o stream de áudio passando os dados para a função de callback."""
        if self.stream is not None:
            return

        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                channels=self.channels,
                callback=callback_function,
                dtype='int16'
                # Se precisar forçar dispositivo: device=1
            )
            self.stream.start()
            self.logger.info("Stream de áudio hardware iniciado.")
        except Exception as e:
            self.logger.critical(f"Erro ao abrir microfone: {e}")
            raise

    def stop_stream(self):
        if self.stream:
            try:
                # 🛑 BALA DE PRATA DO ÁUDIO: abort() em vez de stop()
                # O abort() corta a ligação ao microfone imediatamente, 
                # evitando o deadlock do Windows ao pressionar Ctrl+C.
                self.stream.abort()
                self.stream.close()
            except Exception as e:
                self.logger.warning(f"Aviso ao fechar stream de áudio: {e}")
            finally:
                self.stream = None
                self.logger.info("Stream de áudio cortado.")