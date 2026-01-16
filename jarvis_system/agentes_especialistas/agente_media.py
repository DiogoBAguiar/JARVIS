import pyautogui
from .base_agente import AgenteEspecialista

class AgenteMedia(AgenteEspecialista):
    @property
    def nome(self):
        return "media"

    @property
    def descricao(self):
        """
        Esta descrição ajuda o Cérebro (LLM) a saber quando NÃO chamar este agente.
        """
        return (
            "Agente de CONTROLE DE SISTEMA. "
            "Use apenas para: Pausar, Continuar, Aumentar/Diminuir Volume, Mudo, Próxima/Anterior. "
            "ATENÇÃO: NÃO USE este agente para buscar ou tocar músicas específicas (ex: 'Tocar Coldplay'). "
            "Para tocar artistas ou músicas, use o agente SPOTIFY."
        )

    @property
    def gatilhos(self):
        # REMOVIDO: "tocar", "música", "faixa" (Isso confundia com o Spotify)
        return [
            "pausar", "pausa", "continuar", "play", "stop", "pare", "parar",
            "próxima", "pule", "avançar", "anterior", "voltar",
            "aumentar", "diminuir", "baixar", "volume", "mudo", "silenciar"
        ]

    def executar(self, comando: str, **kwargs) -> str:
        comando = comando.lower()

        # --- CONTROLE DE VOLUME (NOVO) ---
        if "aumentar" in comando or "sobe" in comando:
            pyautogui.press("volumeup", presses=5)
            return "🔊 Volume aumentado."
            
        if "diminuir" in comando or "baixar" in comando:
            pyautogui.press("volumedown", presses=5)
            return "🔉 Volume diminuído."
            
        if "mudo" in comando or "silenciar" in comando:
            pyautogui.press("volumemute")
            return "🔇 Mudo alternado."

        # --- CONTROLE DE REPRODUÇÃO ---
        # Note que removi "tocar" daqui para evitar falsos positivos
        if any(w in comando for w in ["pausar", "pausa", "continuar", "play", "retomar"]):
            pyautogui.press("playpause")
            return "⏯️ Play/Pause acionado."

        if any(w in comando for w in ["parar", "stop", "pare"]):
            pyautogui.press("stop") 
            # Fallback para playpause se o teclado não tiver stop
            pyautogui.press("playpause")
            return "⏹️ Parando mídia."

        if any(w in comando for w in ["próxima", "pule", "avançar", "frente"]):
            pyautogui.press("nexttrack")
            return "⏭️ Próxima faixa."

        if any(w in comando for w in ["anterior", "voltar", "trás", "volta"]):
            pyautogui.press("prevtrack")
            return "⏮️ Faixa anterior."

        return "🤷‍♂️ Comando de mídia não reconhecido ou ambíguo."