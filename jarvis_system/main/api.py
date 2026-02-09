from fastapi import FastAPI
from pydantic import BaseModel
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos
# [IMPORTANTE] Importa o sorteador de frases
from jarvis_system.area_broca.frases_padrao import obter_frase 
from .core import kernel 

app = FastAPI(title="J.A.R.V.I.S. API", version="3.1")

class Command(BaseModel):
    text: str

@app.on_event("startup")
async def startup_event():
    # 1. Inicia o Kernel
    kernel.bootstrap()
    kernel.start_background()
    
    # 2. Sorteia uma frase de boas vindas REAL (ex: "Jarvis online, senhor")
    frase_real = obter_frase("BOAS_VINDAS")
    
    if frase_real:
        # Manda a frase já traduzida. O speak.py vai achar o arquivo .mp3 dela.
        bus.publicar(Evento(Eventos.FALAR, {"texto": frase_real}))
    else:
        # Fallback caso algo dê errado
        bus.publicar(Evento(Eventos.FALAR, {"texto": "Sistemas prontos."}))

@app.on_event("shutdown")
async def shutdown_event():
    kernel.shutdown()

@app.post("/command")
def send_command(cmd: Command):
    if kernel.brain:
        resp = kernel.brain.processar(cmd.text)
        return {"response": resp}
    return {"error": "Brain not ready"}