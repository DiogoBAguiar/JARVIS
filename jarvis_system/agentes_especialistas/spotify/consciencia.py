import time
import psutil
import requests
from .window import WindowManager

class ConscienciaCorporal:
    def __init__(self):
        self.window = WindowManager()
        self.estado_emocional = "NEUTRO" # NEUTRO, CONFUSO, CONFIANTE, FRUSTRADO
        self.erros_consecutivos = 0

    def sentir_sinais_vitais(self):
        """Verifica se o sistema (corpo) está saudável."""
        diagnostico = {
            "internet": self._verificar_internet(),
            "janela_spotify": False,
            "uso_cpu": psutil.cpu_percent(),
            "memoria": psutil.virtual_memory().percent
        }

        # Sente se a janela do Spotify existe
        hwnd = self.window.obter_hwnd()
        if hwnd:
            diagnostico["janela_spotify"] = True
        
        return diagnostico

    def refletir_sobre_acao(self, sucesso: bool, contexto: str):
        """O Agente reflete se mandou bem ou mal."""
        if sucesso:
            self.erros_consecutivos = 0
            self.estado_emocional = "CONFIANTE"
            print(f"😌 [Consciência] Ação '{contexto}' bem sucedida. Sinto-me fluído.")
        else:
            self.erros_consecutivos += 1
            if self.erros_consecutivos > 2:
                self.estado_emocional = "FRUSTRADO"
            else:
                self.estado_emocional = "CONFUSO"
            print(f"😣 [Consciência] Falhei em '{contexto}'. Preciso me adaptar.")

    def _verificar_internet(self):
        try:
            requests.get("https://www.google.com", timeout=2)
            return True
        except:
            return False

    def expressar_estado(self):
        if self.estado_emocional == "FRUSTRADO":
            return "Estou com dificuldades motoras. O Spotify não está respondendo como deveria."
        elif self.estado_emocional == "CONFUSO":
            return "Tentei realizar a ação, mas não tenho certeza se funcionou."
        return "Sistemas operacionais e prontos."