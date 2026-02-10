import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos
# [IMPORTANTE] Importa o sorteador de frases
from jarvis_system.area_broca.frases_padrao import obter_frase 
from .core import kernel 

app = FastAPI(title="J.A.R.V.I.S. API", version="3.2")

class Command(BaseModel):
    text: str

@app.on_event("startup")
async def startup_event():
    print(">>> API STARTUP: Iniciando Kernel...")
    # 1. Inicia o Kernel
    kernel.bootstrap()
    kernel.start_background()
    
    # [FIX] Aguarda 2s para garantir que:
    # a) O barramento de eventos (EventBus) registre todos os assinantes.
    # b) O driver de áudio (NeuralSpeaker) aqueça o buffer para não cortar o som.
    await asyncio.sleep(2.0)
    
    # 2. Sorteia uma frase de boas vindas com INTELIGÊNCIA TEMPORAL
    # forcar_sub_contexto="query" obriga o sistema a escolher uma PERGUNTA
    # Ex: Noite -> "Boa noite, deseja revisar algo?" (query)
    # Ex: Manhã -> "Bom dia, o que deseja fazer?" (query)
    frase_real = obter_frase("BOAS_VINDAS", forcar_sub_contexto="query")
    
    # Fallback: Se não achar uma pergunta (query), tenta qualquer frase de boas vindas
    if not frase_real:
        frase_real = obter_frase("BOAS_VINDAS")
    
    if frase_real:
        print(f">>> BOOT: Frase escolhida: '{frase_real}'")
        # Manda a frase já traduzida. O speak.py vai achar o arquivo .mp3 dela.
        bus.publicar(Evento(Eventos.FALAR, {"texto": frase_real}))
    else:
        # Fallback de segurança se o JSON estiver ilegível
        bus.publicar(Evento(Eventos.FALAR, {"texto": "Sistemas online."}))

@app.on_event("shutdown")
async def shutdown_event():
    kernel.shutdown()

@app.post("/command")
def send_command(cmd: Command):
    if kernel.brain:
        resp = kernel.brain.processar(cmd.text)
        return {"response": resp}
    return {"error": "Brain not ready"}