from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_motor.tool_registry import registry

log = JarvisLogger("SYSTEM_ROOT")

# --- Simulação de Carregamento de Habilidades ---
# Em produção, isso estaria dentro de /agentes_especialistas
@registry.register(name="sistema_ping", description="Verifica latência interna")
def action_ping(echo: str = "pong"):
    """Retorna o eco recebido."""
    import time
    time.sleep(0.1)  # Simula processamento
    return f"ECHO: {echo}"

def wake_up():
    log.info("Iniciando sequência de boot do JARVIS...")
    
    try:
        # 1. Boot do Córtex Motor
        log.info("Carregando ferramentas motoras...")
        tools = registry.list_tools()
        log.info(f"Ferramentas carregadas: {len(tools)}", tools=tools)

        # 2. Teste de Sanidade (Executar uma ação)
        log.info("Executando teste motor...")
        resultado = registry.execute("sistema_ping", echo="Hello World")
        
        log.info("Resultado do teste motor", output=resultado)
        
        log.info("Jarvis operante e aguardando comandos.")
        
    except Exception as e:
        log.error("Falha crítica durante o boot", error_type=type(e).__name__)
        raise

if __name__ == "__main__":
    wake_up()