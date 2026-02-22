import psutil
import pyautogui
import logging

try:
    import screen_brightness_control as sbc
except ImportError:
    sbc = None 

from .base_agente import AgenteEspecialista

# IMPORTAÇÃO DO SEU LANÇADOR INDEXADO (CORRIGIDA)
try:
    from jarvis_system.cortex_motor.appLauncher import launcher as motor_launcher
except ImportError as e:
    motor_launcher = None
    logging.getLogger("AGENTE_SISTEMA").warning(f"Motor Launcher não encontrado: {e}")


class AgenteSistema(AgenteEspecialista):
    """
    Agente de Sistema V3.0 (Integração Direta com Motor Launcher).
    Delega a abertura de aplicativos para o indexador dinâmico, evitando hardcode.
    """
    
    @property
    def nome(self):
        return "sistema"

    @property
    def gatilhos(self):
        return [
            "bateria", "cpu", "memória", "ram", "volume", "som", 
            "brilho", "tela", "sistema", "mudo", "processador",
            "abrir", "iniciar", "executar", "abre", "rodar"
        ]

    def executar(self, comando: str = "", **kwargs) -> str:
        # 1. Desempacotamento flexível (Suporta strings diretas ou kwargs do Orquestrador DAG)
        texto_comando = str(comando) if comando else ""
        
        if kwargs:
            valores_extras = " ".join(str(v) for v in kwargs.values())
            texto_comando = f"{texto_comando} {valores_extras}"
            
        comando_analisado = texto_comando.lower().strip()

        if not comando_analisado:
            return "Comando de sistema vazio."

        # =========================================================
        # DELEGAÇÃO PARA O MOTOR LAUNCHER (O Fim do Hardcode)
        # =========================================================
        # =========================================================
        # DELEGAÇÃO PARA O MOTOR LAUNCHER
        # =========================================================
        palavras_abertura = ["abrir", "iniciar", "executar", "abre", "rodar"]
        if any(palavra in comando_analisado for palavra in palavras_abertura):
            if motor_launcher:
                import logging
                logging.getLogger("AGENTE_SISTEMA").info(f"🚀 Repassando para o Motor Launcher: '{comando_analisado}'")
                
                # Limpa a string para buscar só o nome do app (ex: "abrir calculadora" -> "calculadora")
                alvo = comando_analisado
                for p in palavras_abertura: 
                    alvo = alvo.replace(p, "")
                alvo = alvo.strip()
                
                status, match, caminho = motor_launcher.buscar_candidato(alvo)
                
                if status in ["EXATO", "SUGESTAO"] and caminho:
                    motor_launcher.abrir_por_caminho(caminho)
                    return f"Iniciando: {match}"
                else:
                    # Fallback nativo
                    import subprocess
                    if "bloco de notas" in alvo or "notepad" in alvo:
                        subprocess.Popen("notepad.exe")
                        return "Abrindo o Bloco de Notas."
                    if "calculadora" in alvo or "calc" in alvo:
                        subprocess.Popen("calc.exe")
                        return "Abrindo a Calculadora."
                    return f"Não encontrei nenhum aplicativo '{alvo}' no meu índice."
            else:
                return "O subsistema de inicialização de aplicativos (Motor Launcher) está offline."

        # =========================================================
        # MONITORAMENTO DE HARDWARE E SISTEMA
        # =========================================================
        if "bateria" in comando_analisado:
            if not hasattr(psutil, "sensors_battery"):
                return "Não consigo ler a bateria neste sistema."
                
            bateria = psutil.sensors_battery()
            if not bateria:
                return "Não consigo ler a bateria (talvez seja um Desktop)."
            
            status = "carregando" if bateria.power_plugged else "na bateria"
            return f"A bateria está em {bateria.percent}% e {status}."

        if any(x in comando_analisado for x in ["cpu", "processador"]):
            uso = psutil.cpu_percent(interval=0.5)
            return f"O uso da CPU está em {uso}%."

        if any(x in comando_analisado for x in ["memória", "ram"]):
            mem = psutil.virtual_memory()
            uso_gb = round(mem.used / (1024**3), 1)
            total_gb = round(mem.total / (1024**3), 1)
            return f"Estou usando {uso_gb} Gigas de RAM de um total de {total_gb} Gigas."

        # --- CONTROLE DE VOLUME ---
        if any(x in comando_analisado for x in ["aumentar", "aumenta", "sobe", "mais"]) and ("volume" in comando_analisado or "som" in comando_analisado):
            for _ in range(5): pyautogui.press('volumeup')
            return "Volume aumentado."
        
        if any(x in comando_analisado for x in ["diminuir", "baixar", "diminui", "abaixa", "menos"]):
            for _ in range(5): pyautogui.press('volumedown')
            return "Volume diminuído."
        
        if any(x in comando_analisado for x in ["mudo", "mutar", "silenciar"]):
            pyautogui.press('volumemute')
            return "Áudio mutado."

        # --- BRILHO DA TELA ---
        if "brilho" in comando_analisado:
            if not sbc:
                return "Controle de brilho indisponível."
            try:
                atuais = sbc.get_brightness()
                atual = atuais[0] if isinstance(atuais, list) else atuais
                
                if any(x in comando_analisado for x in ["aumentar", "aumenta", "sobe"]):
                    novo = min(atual + 20, 100)
                    sbc.set_brightness(novo)
                    return f"Brilho aumentado para {novo}%."
                
                elif any(x in comando_analisado for x in ["diminuir", "baixar", "abaixa"]):
                    novo = max(atual - 20, 0)
                    sbc.set_brightness(novo)
                    return f"Brilho reduzido para {novo}%."
                
                return f"O brilho atual é de {atual}%."
            except Exception as e:
                return f"Erro no controle de brilho: {str(e)}"

        return "Comando de sistema não reconhecido."