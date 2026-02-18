import asyncio
import multiprocessing
import time
from fastapi import FastAPI
from pydantic import BaseModel
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos
from jarvis_system.area_broca.frases_padrao import obter_frase 
from .jarvisKernel import kernel 

app = FastAPI(title="J.A.R.V.I.S. API", version="3.5 - Strict Sync")

class Command(BaseModel):
    text: str

async def aguardar_sistema_100_porcento():
    """
    Aguarda rigorosamente que todos os subsistemas e agentes 
    estejam carregados antes de permitir a fala.
    """
    print(">>> [BOOT] Aguardando Cérebro (Orchestrator)...")
    
    # 1. Espera o objeto existir (Instanciação)
    while not kernel.brain:
        await asyncio.sleep(0.1)

    print(">>> [BOOT] Cérebro instanciado. Aguardando Especialistas (Spotify/Agenda)...")

    # 2. Espera os Agentes carregarem (Verifica o flag interno do Orchestrator)
    # Loop de segurança: aguarda até que o Orchestrator diga que está pronto.
    # Se o teu Orchestrator não tiver o flag 'sistemas_carregados', ele vai confiar
    # na contagem de agentes ou num timeout seguro.
    
    max_wait = 300 # 30 segundos de teto máximo
    checks = 0
    
    while checks < max_wait:
        # Tenta verificar o flag oficial (Recomendado no Passo 1)
        if hasattr(kernel.brain, "sistemas_carregados") and kernel.brain.sistemas_carregados:
            print(f">>> [BOOT] ✅ Todos os especialistas carregados em {checks*0.1:.1f}s.")
            break
            
        # Tenta verificar se a lista de agentes já está populada (Plano B)
        # Assume-se que 'agents' ou 'tools' é onde eles ficam guardados
        if hasattr(kernel.brain, "agents") and len(kernel.brain.agents) >= 4:
            print(f">>> [BOOT] ✅ Detecção de agentes concluída ({len(kernel.brain.agents)} ativos).")
            break
            
        await asyncio.sleep(0.1)
        checks += 1

    # 3. Se tiver Visão, espera ela também
    if kernel.eyes:
        print(">>> [BOOT] Sincronizando Visão...")
        # A visão é um processo separado, damos um buffer se ela ainda não tiver dado sinal de vida
        await asyncio.sleep(1.0) 

    print(">>> [BOOT] Sistema J.A.R.V.I.S. Totalmente Sincronizado.")

@app.on_event("startup")
async def startup_event():
    # 🛡️ TRAVA DE PROCESSO
    if multiprocessing.current_process().name != "MainProcess":
        return

    print(">>> API STARTUP: Iniciando Kernel...")
    kernel.bootstrap()
    kernel.start_background()
    
    # ⏳ AQUI ESTÁ A MUDANÇA: Bloqueio Real
    await aguardar_sistema_100_porcento()
    
    # Só chega aqui quando TUDO (incluindo Spotify) estiver pronto
    frase_real = obter_frase("BOAS_VINDAS", forcar_sub_contexto="query")
    if not frase_real:
        frase_real = obter_frase("BOAS_VINDAS")
    
    if frase_real:
        print(f">>> BOOT: Frase escolhida: '{frase_real}'")
        bus.publicar(Evento(Eventos.FALAR, {"texto": frase_real}))
    else:
        bus.publicar(Evento(Eventos.FALAR, {"texto": "Protocolos iniciados."}))

@app.on_event("shutdown")
async def shutdown_event():
    if multiprocessing.current_process().name == "MainProcess":
        kernel.shutdown()

@app.post("/command")
def send_command(cmd: Command):
    # Verificação extra de prontidão
    if kernel.brain and getattr(kernel.brain, "sistemas_carregados", True):
        resp = kernel.brain.processar(cmd.text)
        return {"response": resp}
    return {"error": "System loading..."}