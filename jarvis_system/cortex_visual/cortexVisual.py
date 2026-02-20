import time
import threading
import multiprocessing
import cv2
from multiprocessing import Queue, Event
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento as JarvisEvento
from .configVisao import FACE_CHECK_INTERVAL

# Removi o import global do ObjectDetector daqui para não dar conflito. 
# Ele é importado lá em baixo, de forma segura, dentro da thread (worker).

log = JarvisLogger("CORTEX_VISUAL")

# =====================================================================
# FUNÇÕES AUXILIARES DE RASTREAMENTO E UI
# =====================================================================
def criar_rastreador():
    """Tenta criar um rastreador rápido do OpenCV. Usa o KCF."""
    try:
        return cv2.TrackerKCF_create()
    except AttributeError:
        return cv2.legacy.TrackerKCF_create()

def desenhar_ui(frame, bbox, nome):
    """Desenha a caixa Sci-Fi à volta do rosto na imagem."""
    x, y, w, h = [int(v) for v in bbox]
    cor = (0, 255, 0) if nome != "Desconhecido" else (0, 0, 255)
    
    cv2.rectangle(frame, (x, y), (x + w, y + h), cor, 1)
    cv2.rectangle(frame, (x, y + h - 25), (x + w, y + h), cor, cv2.FILLED)
    cv2.putText(frame, nome.upper(), (x + 5, y + h - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

def caixas_sobrepostas(bbox1, bbox2):
    """VERIFICAÇÃO ESPACIAL: Avalia se duas caixas são da mesma pessoa baseado na posição"""
    x1, y1, w1, h1 = bbox1
    x2, y2, w2, h2 = bbox2
    
    cx1, cy1 = x1 + w1/2, y1 + h1/2
    cx2, cy2 = x2 + w2/2, y2 + h2/2
    
    dist = ((cx1 - cx2)**2 + (cy1 - cy2)**2)**0.5
    limite = max(w1, w2) / 1.2
    return dist < limite

# =====================================================================
# WORKER PRINCIPAL DE VISÃO
# =====================================================================
def vision_worker(queue_out, video_queue, telemetry_queue, stop_event):
    eyes = None
    try:
        from .cameraDriver import CameraDriver
        from .face_id import BiometricSystem
        
        eyes = CameraDriver()
        face_id = BiometricSystem()
        eyes.start()

        try:
            from .hand_sensor import HandSensor
            hand_sensor = HandSensor()
        except Exception:
            hand_sensor = None
            
        try:
            from .emotion_sensor import EmotionSensor
            from .object_sensor import ObjectDetector
            emotion_sensor = EmotionSensor()
            object_sensor = ObjectDetector()
            log.info("🎯 Sensores de Emoção e Objetos Carregados com Sucesso!")
        except Exception as e:
            log.error(f"Erro ao carregar novos sensores: {e}")
            emotion_sensor, object_sensor = None, None

        last_seen_cache = {}
        
        if eyes and face_id:
            log.info("👁️ Processo Visual Online (Modo Tracking com Memória Espacial).")

        rastreadores_ativos = [] 
        contador_frames = 0
        FRAMES_PARA_REDETECTAR = 30 

        while not stop_event.is_set():
            frame = eyes.get_frame()
            if frame is None: continue

            contador_frames += 1
            precisa_redetectar = (contador_frames >= FRAMES_PARA_REDETECTAR) or (len(rastreadores_ativos) == 0)

            # -------------------------------------------------------------
            # FASE 1: O "CAÇADOR" (IA PESADA - Roda a cada 30 frames)
            # -------------------------------------------------------------
            if precisa_redetectar:
                resultados = face_id.identify(frame)
                novos_rastreadores = [] 
                
                # --- NOVIDADE: YOLO ENTRA EM AÇÃO AQUI ---
                # Roda o YOLO apenas a cada 30 frames para não sobrecarregar
                if object_sensor:
                    objetos_agora = object_sensor.processar(frame)
                    for obj in objetos_agora:
                        queue_out.put(("OBJETO_DETECTADO", obj))
                        log.info(f"🔎 Objeto visto: {obj}")
                
                for res in resultados:
                    nome_detectado = res["nome"]
                    nova_bbox = res["bbox"]
                    nome_final = nome_detectado
                    
                    for rastreador_antigo in rastreadores_ativos:
                        if caixas_sobrepostas(nova_bbox, rastreador_antigo["bbox"]):
                            if nome_detectado == "Desconhecido" and rastreador_antigo["nome"] != "Desconhecido":
                                nome_final = rastreador_antigo["nome"]
                            break
                    
                    tracker = criar_rastreador()
                    tracker.init(frame, nova_bbox)
                    
                    novos_rastreadores.append({
                        "nome": nome_final,
                        "tracker": tracker,
                        "bbox": nova_bbox
                    })
                    
                    now = time.time()
                    if nome_final != "Desconhecido" and (now - last_seen_cache.get(nome_final, 0)) > 60:
                        queue_out.put(("ROSTO_IDENTIFICADO", nome_final))
                        last_seen_cache[nome_final] = now
                        
                    desenhar_ui(frame, nova_bbox, nome_final)
                    
                rastreadores_ativos = novos_rastreadores
                contador_frames = 0
                
            # -------------------------------------------------------------
            # FASE 2: O "CÃO DE GUARDA" (RASTREAMENTO RÁPIDO OpenCV)
            # -------------------------------------------------------------
            else:
                trackers_falharam = False
                for rastreador in rastreadores_ativos:
                    sucesso, nova_bbox = rastreador["tracker"].update(frame)
                    
                    if sucesso:
                        rastreador["bbox"] = nova_bbox
                        desenhar_ui(frame, nova_bbox, rastreador["nome"])
                    else:
                        trackers_falharam = True
                
                if trackers_falharam:
                    contador_frames = FRAMES_PARA_REDETECTAR

            # --- GESTOS E EMOÇÕES ---
            gesto_atual = "---"
            emocao_atual = "---"
            
            # Converte a imagem para o MediaPipe (Ele exige formato RGB)
            # Fazemos isto 1 vez só para poupar CPU para as Mãos e Emoções
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            if hand_sensor:
                gesto = hand_sensor.processar(rgb_frame)
                if gesto:
                    gesto_atual = gesto
                    if gesto not in ["NEUTRO", "PUNHO FECHADO"]: 
                        queue_out.put(("GESTO_DETECTADO", gesto))

            # --- NOVIDADE: EMOÇÕES ENTRAM AQUI ---
            if emotion_sensor:
                emocao = emotion_sensor.processar(rgb_frame)
                if emocao:
                    emocao_atual = emocao
                    if emocao != "NEUTRO": 
                        queue_out.put(("EMOCAO_DETECTADA", emocao))

            # --- TRANSMISSÃO ---
            if video_queue and not video_queue.full():
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
                if ret: video_queue.put(buffer.tobytes())

            if telemetry_queue and not telemetry_queue.full():
                # Agora enviamos a emoção atualizada para o Frontend Web!
                telemetry_queue.put({"fps": 30, "hand": {"gesture": gesto_atual, "emotion": emocao_atual, "x":0, "y":0}})

            time.sleep(0.01)

    except KeyboardInterrupt:
        pass 
    except Exception as e:
        log.error(f"Erro fatal no worker: {e}")
    finally:
        try:
            if eyes: eyes.stop()
        except (KeyboardInterrupt, Exception):
            pass
        print("👁️ Processo Visual Encerrado.")

# =====================================================================
# CLASSE DE GERENCIAMENTO
# =====================================================================
class VisualCortex:
    def __init__(self, video_queue=None, telemetry_queue=None):
        self.process = None
        self.queue = Queue()
        self.stop_event = multiprocessing.Event()
        self.video_queue = video_queue
        self.telemetry_queue = telemetry_queue
        self.running = False

    def start(self):
        log.info("👁️ Iniciando Córtex Visual...")
        self.stop_event.clear()
        self.process = multiprocessing.Process(
            target=vision_worker, 
            args=(self.queue, self.video_queue, self.telemetry_queue, self.stop_event),
            name="Jarvis_Vision_Core"
        )
        self.process.daemon = True
        self.process.start()
        self.running = True
        threading.Thread(target=self._listen_queue, daemon=True).start()

    def _listen_queue(self):
        """Ouve os sinais da fila do Worker e transforma em Eventos Globais do Jarvis."""
        while self.running:
            try:
                tipo, dado = self.queue.get(timeout=1)
                
                if tipo == "ROSTO_IDENTIFICADO":
                    bus.publicar(JarvisEvento("VISAO_ROSTO_IDENTIFICADO", {"nome": dado}))
                elif tipo == "GESTO_DETECTADO":
                    bus.publicar(JarvisEvento("VISAO_GESTO", {"gesto": dado}))
                # --- NOVIDADES: ESCUTAR OBJETOS E EMOÇÕES ---
                elif tipo == "OBJETO_DETECTADO":
                    bus.publicar(JarvisEvento("VISAO_OBJETO", {"objeto": dado}))
                elif tipo == "EMOCAO_DETECTADA":
                    bus.publicar(JarvisEvento("VISAO_EMOCAO", {"emocao": dado}))
                    
            except: continue

    def stop(self):
        log.info("👁️ Iniciando protocolo de desligamento do Córtex Visual...")
        self.running = False
        self.stop_event.set() 
        
        if self.process and self.process.is_alive():
            self.process.join(timeout=2)
            if self.process.is_alive():
                log.warning("⚠️ O processo visual está bloqueado. A forçar o encerramento (SIGTERM)...")
                self.process.terminate() 
                self.process.join(timeout=1) 
                log.info("👁️ Processo visual encerrado à força.")
            else:
                log.info("👁️ Processo visual encerrado graciosamente.")

vision = VisualCortex()