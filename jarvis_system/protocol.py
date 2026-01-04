"""
Protocolo Oficial de Comunicação do Jarvis.
Define os contratos de eventos para garantir tipagem, consistência e 
estados para feedback visual (UI).
"""

class Eventos:
    # --- Input Sensorial (Área de Wernicke) ---
    # Disparado quando a STT (Speech-to-Text) detecta uma frase finalizada
    # Payload: {"texto": "comando do usuario"}
    FALA_RECONHECIDA = "input:fala_reconhecida"
    
    # --- Processamento Cognitivo (Córtex Frontal) ---
    # Disparado quando o Orchestrator envia o prompt para a LLM
    # Útil para UI mostrar animação de "loading/girando"
    # Payload: {"prompt": "texto enviado..."}
    PENSANDO = "cortex:pensando"

    # --- Output Motor (Área de Broca & Motor) ---
    # Disparado quando o sistema decide falar algo (TTS)
    # Payload: {"texto": "resposta do sistema"}
    FALAR = "output:falar"
    
    # Disparado para ações físicas ou de sistema
    # Payload: {"comando": "abrir_calculadora", "status": "sucesso/erro"}
    EXECUTAR_FERRAMENTA = "output:ferramenta"
    
    # Disparado para ações do mouse (opcional, se usar automação visual)
    # Payload: {"tipo": "clique" | "mover", "x": 0, "y": 0}
    MOUSE = "output:mouse"

    # --- Sistema (Controle & Observabilidade) ---
    # Logs gerais para debug
    LOG = "system:log"
    
    # Erros críticos para notificação visual (vermelho na UI)
    # Payload: {"erro": "mensagem do erro", "modulo": "origem"}
    ERRO = "system:erro"
    
    # Sinal de encerramento total
    SHUTDOWN = "system:shutdown"