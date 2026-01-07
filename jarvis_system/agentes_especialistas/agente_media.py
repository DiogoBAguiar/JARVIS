import pyautogui
from .base_agente import AgenteEspecialista

class AgenteMedia(AgenteEspecialista):
    @property
    def nome(self):
        return "media"

    @property
    def gatilhos(self):
        return [
            "pausar", "pausa", "continuar", "play", "stop", "pare", "parar",
            "próxima", "pule", "avançar", "anterior", "voltar", "música", "faixa"
        ]

    def executar(self, comando: str, **kwargs) -> str:
        comando = comando.lower()

        # Play / Pause
        if any(w in comando for w in ["pausar", "pausa", "continuar", "play", "tocar"]):
            pyautogui.press("playpause")
            return "Feito."

        # Stop
        if any(w in comando for w in ["parar", "stop", "pare"]):
            pyautogui.press("stop") # Nem todos teclados tem isso, mas tentamos
            return "Parando reprodução."

        # Próxima (Next)
        if any(w in comando for w in ["próxima", "pule", "avançar", "frente"]):
            pyautogui.press("nexttrack")
            return "Próxima faixa."

        # Anterior (Prev)
        if any(w in comando for w in ["anterior", "voltar", "trás", "volta"]):
            pyautogui.press("prevtrack")
            return "Faixa anterior."

        return "Comando de mídia não reconhecido."