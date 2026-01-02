import os
import subprocess
import platform
from jarvis_system.cortex_motor.tool_registry import registry
from jarvis_system.cortex_frontal.observability import JarvisLogger

log = JarvisLogger("MOTOR_OS")

# --- Ferramentas de Sistema Operacional ---

@registry.register(name="abrir_calculadora", description="Abre a calculadora do Windows")
def open_calculator():
    """Abre a calculadora nativa."""
    system = platform.system()
    try:
        if system == "Windows":
            subprocess.Popen("calc.exe")
        elif system == "Linux":
            subprocess.Popen(["gnome-calculator"]) 
        elif system == "Darwin":
            subprocess.Popen(["open", "-a", "Calculator"])
        return "Calculadora iniciada."
    except Exception as e:
        log.error("Erro ao abrir calculadora", error=str(e))
        return "Falha ao abrir calculadora."

@registry.register(name="abrir_bloco_notas", description="Abre o editor de texto simples")
def open_notepad():
    """Abre o Bloco de Notas."""
    try:
        if platform.system() == "Windows":
            subprocess.Popen("notepad.exe")
            return "Bloco de notas aberto."
        else:
            return "Comando disponível apenas para Windows."
    except Exception as e:
        return f"Erro: {str(e)}"

# --- CORREÇÃO: ADICIONADA A FERRAMENTA FALTANTE ---
@registry.register(name="sistema_ping", description="Verificação de status")
def system_ping():
    """Responde ao comando de status."""
    return "Todos os sistemas operacionais. Pronto para uso."

@registry.register(name="sistema_desligar", description="Desliga o Jarvis", safe_mode=False)
def shutdown_jarvis():
    """Retorna um sinal especial para o orquestrador."""
    return "__SHUTDOWN_SIGNAL__"