from fastapi import FastAPI
from pydantic import BaseModel
# Importação relativa funciona bem aqui porque são do mesmo pacote
from .core import kernel 

app = FastAPI(title="J.A.R.V.I.S. API", version="3.1")

class Command(BaseModel):
    text: str

@app.on_event("startup")
async def startup_event():
    # O Kernel acorda junto com o servidor
    kernel.bootstrap()
    kernel.start_background()

@app.on_event("shutdown")
async def shutdown_event():
    kernel.shutdown()

@app.post("/command")
def send_command(cmd: Command):
    """Permite enviar comandos de texto via API."""
    if kernel.brain:
        resp = kernel.brain.processar(cmd.text)
        return {"response": resp}
    return {"error": "Brain not ready"}