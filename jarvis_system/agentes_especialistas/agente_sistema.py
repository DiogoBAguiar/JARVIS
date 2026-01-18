import psutil
import pyautogui
try:
    import screen_brightness_control as sbc
except ImportError:
    sbc = None 

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

    # --- CORREÇÃO: Voltamos para 'executar' para respeitar a BaseAgente ---
    def executar(self, comando: str, **kwargs) -> str:
        comando = comando.lower()

        # --- MONITORAMENTO ---
        if "bateria" in comando:
            if not hasattr(psutil, "sensors_battery"):
                return "Não consigo ler a bateria neste sistema."
                
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

        # --- CONTROLE DE VOLUME ---
        if any(x in comando for x in ["aumentar", "aumenta", "sobe", "mais"]) and ("volume" in comando or "som" in comando):
            for _ in range(5): pyautogui.press('volumeup')
            return "Volume aumentado."
        
        if any(x in comando for x in ["diminuir", "baixar", "diminui", "abaixa", "menos"]):
            for _ in range(5): pyautogui.press('volumedown')
            return "Volume diminuído."
        
        if "mudo" in comando or "mutar" in comando or "silenciar" in comando:
            pyautogui.press('volumemute')
            return "Áudio mutado."

        # --- BRILHO ---
        if "brilho" in comando:
            if not sbc:
                return "Controle de brilho indisponível."
            try:
                atuais = sbc.get_brightness()
                atual = atuais[0] if isinstance(atuais, list) else atuais
                
                if any(x in comando for x in ["aumentar", "aumenta", "sobe"]):
                    novo = min(atual + 20, 100)
                    sbc.set_brightness(novo)
                    return f"Brilho aumentado para {novo}%."
                
                elif any(x in comando for x in ["diminuir", "baixar", "abaixa"]):
                    novo = max(atual - 20, 0)
                    sbc.set_brightness(novo)
                    return f"Brilho reduzido para {novo}%."
                
                return f"O brilho atual é de {atual}%."
            except Exception as e:
                return f"Erro no brilho: {str(e)}"

        return "Comando de sistema não reconhecido."