import os
import subprocess
import platform
import ctypes
import sys
from datetime import datetime

# Imports do Core
from jarvis_system.cortex_motor.tool_registry import registry
from jarvis_system.cortex_frontal.observability import JarvisLogger

log = JarvisLogger("MOTOR_OS")

# --- UTILITÁRIOS NATIVOS DO WINDOWS ---

@registry.register(name="abrir_calculadora", description="Abre a calculadora do sistema")
def open_calculator():
    """Abre a calculadora nativa de forma não bloqueante."""
    system = platform.system()
    try:
        if system == "Windows":
            subprocess.Popen("calc.exe")
        elif system == "Linux":
            subprocess.Popen(["gnome-calculator"], stderr=subprocess.DEVNULL) 
        elif system == "Darwin":
            subprocess.Popen(["open", "-a", "Calculator"])
        
        return "Calculadora exibida na tela."
    except Exception as e:
        log.error(f"Erro ao abrir calculadora: {e}")
        return "Não consegui abrir a calculadora."

@registry.register(name="abrir_bloco_notas", description="Abre o Bloco de Notas (Notepad)")
def open_notepad():
    """Abre o Bloco de Notas."""
    try:
        if platform.system() == "Windows":
            subprocess.Popen("notepad.exe")
            return "Bloco de notas aberto para escrita."
        else:
            return "Ferramenta exclusiva para Windows."
    except Exception as e:
        log.error(f"Erro ao abrir notepad: {e}")
        return f"Erro: {str(e)}"

@registry.register(name="abrir_cmd", description="Abre um terminal de comando")
def open_terminal():
    """Abre o CMD ou PowerShell."""
    try:
        if platform.system() == "Windows":
            subprocess.Popen("start cmd.exe", shell=True)
            return "Terminal de comando iniciado."
        return "Terminal não suportado neste SO."
    except Exception as e:
        return f"Erro ao abrir terminal: {e}"

# --- CONTROLE DE MÍDIA E VOLUME (ESSENCIAL) ---
# Usa ctypes para enviar comandos de teclado multimídia virtuais

@registry.register(name="sistema_volume_aumentar", description="Aumenta o volume do sistema")
def volume_up():
    if platform.system() == "Windows":
        # VK_VOLUME_UP = 0xAF
        for _ in range(5): # Aumenta 5 'ticks'
            ctypes.windll.user32.keybd_event(0xAF, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0xAF, 0, 2, 0)
        return "Volume aumentado."
    return "Controle de volume indisponível."

@registry.register(name="sistema_volume_diminuir", description="Diminui o volume do sistema")
def volume_down():
    if platform.system() == "Windows":
        # VK_VOLUME_DOWN = 0xAE
        for _ in range(5):
            ctypes.windll.user32.keybd_event(0xAE, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0xAE, 0, 2, 0)
        return "Volume diminuído."
    return "Controle de volume indisponível."

@registry.register(name="sistema_mudo", description="Ativa/Desativa mudo")
def volume_mute():
    if platform.system() == "Windows":
        # VK_VOLUME_MUTE = 0xAD
        ctypes.windll.user32.keybd_event(0xAD, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0xAD, 0, 2, 0)
        return "Audio alternado (Mute/Unmute)."
    return "Controle de volume indisponível."

# --- FERRAMENTAS DE DIAGNÓSTICO ---

@registry.register(name="sistema_ping", description="Verificação de status e hora")
def system_ping():
    """Retorna status operacional e hora atual."""
    now = datetime.now().strftime("%H:%M")
    sistema = f"{platform.system()} {platform.release()}"
    return f"Sistemas online. Rodando em {sistema}. Hora local: {now}."

@registry.register(name="sistema_info", description="Informações de hardware")
def system_info():
    """Retorna detalhes da máquina."""
    arch = platform.machine()
    proc = platform.processor()
    return f"Arquitetura: {arch}. Processador: {proc}. Python: {sys.version.split()[0]}."

@registry.register(name="sistema_desligar", description="Desliga o Jarvis", safe_mode=False)
def shutdown_jarvis():
    """
    Nota: O Orquestrador intercepta este comando antes de chegar aqui para fazer o Graceful Shutdown via EventBus.
    Mantido aqui para documentação do Registry.
    """
    return "__SHUTDOWN_SIGNAL__"