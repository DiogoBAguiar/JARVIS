# jarvis_system/area_broca/listen/transcriber.py
import numpy as np
import logging
from faster_whisper import WhisperModel

class WhisperTranscriber:
    def __init__(self, model_size="base", device="cpu", compute_type="int8"):
        self.logger = logging.getLogger("BROCA_WHISPER")
        self.logger.info(f"Carregando Whisper ({model_size}) em {device}...")
        try:
            self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
            self.logger.info("Whisper carregado com sucesso.")
        except Exception as e:
            self.logger.critical(f"Erro ao carregar Whisper: {e}")
            raise

    def transcribe(self, audio_buffer_float):
        """
        Recebe uma lista de buffers float, concatena e transcreve.
        """
        if not audio_buffer_float:
            return ""

        try:
            audio_final = np.concatenate(audio_buffer_float)
            
            segments, _ = self.model.transcribe(
                audio_final,
                beam_size=5,
                language="pt",
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
                condition_on_previous_text=False
            )

            texto_acumulado = []
            for segment in segments:
                if segment.no_speech_prob < 0.6:
                    texto_acumulado.append(segment.text)

            return " ".join(texto_acumulado).strip()
            
        except Exception as e:
            self.logger.error(f"Erro na inferência: {e}")
            return ""