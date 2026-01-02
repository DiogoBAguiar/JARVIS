"""
Protocolo Oficial de Comunicação do Jarvis.
Define os contratos de eventos para garantir tipagem e consistência.
"""

class Eventos:
    # --- Input Sensorial (Entrada) ---
    # Disparado quando a STT (Speech-to-Text) detecta uma frase finalizada
    # Payload: {"texto": "comando do usuario"}
    FALA_RECONHECIDA = "input:fala_reconhecida"
    
    # --- Output Motor (Saída) ---
    # Disparado quando o sistema decide falar algo
    # Payload: {"texto": "resposta do sistema"}
    FALAR = "output:falar"
    
    # Disparado para ações do mouse
    # Payload: {"tipo": "clique" | "mover", ...}
    MOUSE = "output:mouse"

    # --- Sistema (Controle) ---
    # Logs críticos que devem aparecer na UI ou serem persistidos
    LOG = "system:log"
    
    # Sinal de encerramento
    SHUTDOWN = "system:shutdown"