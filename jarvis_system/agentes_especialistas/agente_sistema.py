import psutil
import pyautogui
import platform
try:
    import screen_brightness_control as sbc
except:
    sbc = None # Fallback se não der certo ou for Desktop sem monitor compatível

from .base_agente import AgenteEspecialista

class AgenteSistema(AgenteEspecialista):
    @property
    def nome(self):
        return "sistema"

    @property
    def gatilhos(self):
        return [
            "bateria", "cpu", "memória", "ram", "volume", "som", 
            "brilho", "tela", "sistema", "mudo", "processador"
        ]

    def executar(self, comando: str, **kwargs) -> str:
        comando = comando.lower()

        # --- MONITORAMENTO ---
        if "bateria" in comando:
            bateria = psutil.sensors_battery()
            if not bateria:
                return "Não consigo ler a bateria (talvez seja um Desktop)."
            
            status = "carregando" if bateria.power_plugged else "na bateria"
            return f"A bateria está em {bateria.percent}% e {status}."

        if any(x in comando for x in ["cpu", "processador"]):
            uso = psutil.cpu_percent(interval=0.5)
            return f"O uso da CPU está em {uso}%."

        if any(x in comando for x in ["memória", "ram"]):
            mem = psutil.virtual_memory()
            uso_gb = round(mem.used / (1024**3), 1)
            total_gb = round(mem.total / (1024**3), 1)
            return f"Estou usando {uso_gb} Gigas de RAM de um total de {total_gb} Gigas."

        # --- CONTROLE DE VOLUME (Simulando Teclas) ---
        if "aumentar" in comando and ("volume" in comando or "som" in comando):
            for _ in range(5): pyautogui.press('volumeup')
            return "Aumentando o volume."
        
        if "diminuir" in comando or "baixar" in comando:
            for _ in range(5): pyautogui.press('volumedown')
            return "Baixando o volume."
        
        if "mudo" in comando or "mutar" in comando:
            pyautogui.press('volumemute')
            return "Áudio mutado."

        # --- BRILHO (Funciona melhor em Notebooks) ---
        if "brilho" in comando and sbc:
            try:
                if "aumentar" in comando:
                    atual = sbc.get_brightness()
                    novo = min(atual[0] + 20, 100)
                    sbc.set_brightness(novo)
                    return f"Brilho aumentado para {novo}%."
                elif "diminuir" in comando:
                    atual = sbc.get_brightness()
                    novo = max(atual[0] - 20, 0)
                    sbc.set_brightness(novo)
                    return f"Brilho reduzido para {novo}%."
            except:
                return "Não consegui controlar o brilho do monitor."

        return "Comando de sistema não reconhecido."