"""
Protocolo Oficial de Comunicação do Jarvis.
Define os contratos de eventos para garantir tipagem, consistência e 
estados para feedback visual (UI).
"""

class Eventos:
    # --- Input Sensorial (Área de Wernicke) ---
    FALA_RECONHECIDA = "input:fala_reconhecida"
    
    # --- Processamento Cognitivo (Córtex Frontal) ---
    PENSANDO = "cortex:pensando"

    # --- Output Motor (Área de Broca & Motor) ---
    FALAR = "output:falar"
    EXECUTAR_FERRAMENTA = "output:ferramenta"
    MOUSE = "output:mouse"

    # --- Sistema (Controle & Observabilidade) ---
    LOG = "system:log"
    ERRO = "system:erro"
    SHUTDOWN = "system:shutdown"

    # --- NOVO: Controle de Estado (Sincronização de Fala) ---
    # Usado para evitar que o Jarvis ouça a si mesmo
    # Payload: {"status": True} (Falando) | {"status": False} (Silêncio)
    STATUS_FALA = "system:status_fala"