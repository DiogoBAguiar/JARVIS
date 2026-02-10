import os
import cv2
import face_recognition
import numpy as np
import psutil
import time
import datetime
from flask import Flask, render_template, Response, jsonify

# --- CONFIGURAÇÃO ---
app = Flask(__name__)

# Caminho da Memória
base_dir = os.path.dirname(os.path.abspath(__file__))
# Tenta subir niveis até achar a pasta data
path_candidate = os.path.join(base_dir, '..', '..', 'jarvis_system', 'data', 'visual_memory') 
# Ajuste fino se necessário, o script tenta achar a pasta
if not os.path.exists(path_candidate):
     path_candidate = os.path.join(base_dir, '..', 'data', 'visual_memory')

MEMORY_PATH = os.path.abspath(path_candidate)

# Variáveis Globais para compartilhar dados entre Threads
system_state = {
    "target_name": "AGUARDANDO...",
    "target_status": "SCANNING",
    "cpu_percent": 0,
    "ram_percent": 0,
    "ram_used": 0,
    "ram_total": 0,
    "boot_time": datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%H:%M:%S")
}

# --- CARREGAR MEMÓRIA ---
known_face_encodings = []
known_face_names = []

def load_memory():
    print(f"📂 Carregando memória de: {MEMORY_PATH}")
    if os.path.exists(MEMORY_PATH):
        for file in os.listdir(MEMORY_PATH):
            if file.endswith(('.jpg', '.png')):
                name = os.path.splitext(file)[0].replace("_", " ").upper()
                path = os.path.join(MEMORY_PATH, file)
                try:
                    img = face_recognition.load_image_file(path)
                    encoding = face_recognition.face_encodings(img)[0]
                    known_face_encodings.append(encoding)
                    known_face_names.append(name)
                    print(f"✅ Identidade: {name}")
                except:
                    pass
    else:
        print("⚠️ Pasta visual_memory não encontrada.")

load_memory()

# --- LOOP DE VÍDEO ---
def gen_frames():
    camera = cv2.VideoCapture(0)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    while True:
        success, frame = camera.read()
        if not success: break
        
        # 1. Processamento de Imagem (Reduzido para performance)
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = np.ascontiguousarray(small_frame[:, :, ::-1])

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        target_name = "NENHUM ALVO"
        status = "BUSCANDO..."

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
            name = "DESCONHECIDO"
            status = "ANALISANDO..."

            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            
            if matches[best_match_index]:
                name = known_face_names[best_match_index]
                status = "IDENTIFICADO"

            face_names.append(name)
            target_name = name

        # Atualiza o Estado Global (para a API ler)
        system_state["target_name"] = target_name
        system_state["target_status"] = status

        # 2. Desenho na Tela (HUD)
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            top *= 4; right *= 4; bottom *= 4; left *= 4
            color = (0, 255, 0) if name != "DESCONHECIDO" else (0, 0, 255) # Verde ou Vermelho
            
            # Caixa futurista (apenas cantos)
            l = 30
            t = 2
            # Top-Left
            cv2.line(frame, (left, top), (left + l, top), color, t)
            cv2.line(frame, (left, top), (left, top + l), color, t)
            # Top-Right
            cv2.line(frame, (right, top), (right - l, top), color, t)
            cv2.line(frame, (right, top), (right, top + l), color, t)
            # Bottom-Left
            cv2.line(frame, (left, bottom), (left + l, bottom), color, t)
            cv2.line(frame, (left, bottom), (left, bottom - l), color, t)
            # Bottom-Right
            cv2.line(frame, (right, bottom), (right - l, bottom), color, t)
            cv2.line(frame, (right, bottom), (right, bottom - l), color, t)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# --- ROTAS ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/telemetry')
def telemetry():
    # Atualiza dados do hardware em tempo real
    system_state["cpu_percent"] = psutil.cpu_percent()
    mem = psutil.virtual_memory()
    system_state["ram_percent"] = mem.percent
    system_state["ram_used"] = round(mem.used / (1024**3), 1)
    system_state["ram_total"] = round(mem.total / (1024**3), 1)
    
    return jsonify(system_state)

if __name__ == '__main__':
    print("🚀 JARVIS HUD SERVER ONLINE em http://127.0.0.1:5000")
    app.run(debug=True, threaded=True)