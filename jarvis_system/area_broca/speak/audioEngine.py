# jarvis_system/area_broca/speak/engine.py
import pygame
import pyttsx3
import time

class AudioEngine:
    def __init__(self, logger):
        self.log = logger
        self._inicializar_mixer()
        try:
            self.offline_engine = pyttsx3.init()
        except:
            self.offline_engine = None

    def _inicializar_mixer(self):
        try:
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=4096)
            pygame.mixer.init()
        except Exception as e:
            self.log.warning(f"Mixer High-Buffer falhou: {e}")
            try: pygame.mixer.init()
            except: pass

    def play_file(self, file_path, stop_event):
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy() and not stop_event.is_set():
                pygame.time.Clock().tick(10)
        except Exception as e:
            self.log.error(f"Erro playback: {e}")

    def speak_offline(self, text):
        if self.offline_engine:
            try:
                self.offline_engine.say(text)
                self.offline_engine.runAndWait()
            except: pass