import asyncio
import multiprocessing
import time
import os
import json
import queue # <--- NECESSÁRIO PARA LER AS FILAS
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles 
from pydantic import BaseModel
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos
from jarvis_system.area_broca.frases_padrao import obter_frase 
from .jarvisKernel import kernel 

app = FastAPI(title="J.A.R.V.I.S. API", version="3.8 - Live Vision")

# -------------------------------------------------------------------------
# 📡 GESTOR DE CONEXÕES (WEBSOCKETS)
# -------------------------------------------------------------------------
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f">>> [API] Cliente conectado: {websocket.client.host}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, data: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception:
                self.disconnect(connection)

ws_manager = ConnectionManager()

# -------------------------------------------------------------------------
# 🎨 FRONT-END SETUP
# -------------------------------------------------------------------------
templates = Jinja2Templates(directory="jarvis_system/front-end/templates")
static_path = os.path.join("jarvis_system", "front-end", "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

class Command(BaseModel):
    text: str

# -------------------------------------------------------------------------
# 📹 GERADOR DE VÍDEO REAL (Conectado ao Kernel)
# -------------------------------------------------------------------------
def gerar_frames_reais():
    """Lê frames da fila do Kernel e envia para o navegador"""
    while True:
        # Se o kernel tiver a fila de vídeo instanciada
        if kernel.video_queue:
            try:
                # Tenta pegar um frame (espera máx 0.2s)
                frame_bytes = kernel.video_queue.get(timeout=0.2)
                
                # Formata como Multipart (MJPEG Standard)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            except queue.Empty:
                # Se não houver frame novo, dorme um pouco para não fritar a CPU
                time.sleep(0.05)
        else:
            # Kernel ainda não iniciou a visão
            time.sleep(1) 

# -------------------------------------------------------------------------
# ⏳ LÓGICA DE SINCRONIZAÇÃO
# -------------------------------------------------------------------------
async def aguardar_sistema_100_porcento():
    print(">>> [BOOT] Aguardando Cérebro (Orchestrator)...")
    while not kernel.brain:
        await asyncio.sleep(0.1)

    print(">>> [BOOT] Cérebro instanciado. Sincronizando...")
    max_wait = 300
    checks = 0
    while checks < max_wait:
        if hasattr(kernel.brain, "sistemas_carregados") and kernel.brain.sistemas_carregados:
            print(f">>> [BOOT] ✅ Sistemas carregados em {checks*0.1:.1f}s.")
            break
        await asyncio.sleep(0.1)
        checks += 1

    if kernel.eyes:
        print(">>> [BOOT] Sincronizando Visão...")
        await asyncio.sleep(1.0) 

    print(">>> [BOOT] Sistema J.A.R.V.I.S. Totalmente Sincronizado.")

# -------------------------------------------------------------------------
# 🚀 EVENTOS DE STARTUP
# -------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    if multiprocessing.current_process().name != "MainProcess":
        return

    print(">>> API STARTUP: Iniciando Kernel...")
    kernel.bootstrap()
    kernel.start_background()
    
    await aguardar_sistema_100_porcento()
    
    frase_real = obter_frase("BOAS_VINDAS", forcar_sub_contexto="query")
    if not frase_real: frase_real = obter_frase("BOAS_VINDAS")
    
    bus.publicar(Evento(Eventos.FALAR, {"texto": frase_real or "Online."}))

@app.on_event("shutdown")
async def shutdown_event():
    if multiprocessing.current_process().name == "MainProcess":
        kernel.shutdown()

# -------------------------------------------------------------------------
# 🌐 ROTAS DA API
# -------------------------------------------------------------------------

@app.get("/dashboard")
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

# ✅ ROTA WEBSOCKET (DADOS REAIS)
# No api.py, dentro do websocket_endpoint:

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Aceita a conexão imediatamente
    await websocket.accept()
    ws_manager.active_connections.append(websocket)
    
    try:
        while True:
            # 1. Envia telemetria se houver
            if kernel.telemetry_queue and not kernel.telemetry_queue.empty():
                try:
                    data = kernel.telemetry_queue.get_nowait()
                    await websocket.send_json({"type": "telemetry", **data})
                except: pass
            
            # 2. Tenta ler mensagens do front sem travar o loop
            try:
                # Usamos um timeout minúsculo para não bloquear a fila de telemetria
                await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
            except asyncio.TimeoutError:
                pass
            except Exception:
                break # Sai do loop se a conexão falhar
                
            await asyncio.sleep(0.05) # Dá fôlego ao CPU
            
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(websocket)

# ✅ ROTA DE VÍDEO (IMAGENS REAIS)
@app.get("/video_feed")
def video_feed():
    # Usa a função 'gerar_frames_reais' definida acima
    return StreamingResponse(
        gerar_frames_reais(), 
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.post("/command")
def send_command(cmd: Command):
    if kernel.brain and getattr(kernel.brain, "sistemas_carregados", True):
        resp = kernel.brain.processar(cmd.text)
        return {"response": resp}
    return {"error": "System loading..."}