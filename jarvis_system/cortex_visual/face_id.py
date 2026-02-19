import os
import cv2
import face_recognition
import numpy as np
import mediapipe as mp
from jarvis_system.cortex_frontal.observability import JarvisLogger
from .configVisao import MEMORY_PATH, TOLERANCE

log = JarvisLogger("VISUAL_FACEID")

class BiometricSystem:
    def __init__(self):
        self.known_encodings = []
        self.known_names = []
        
        # --- MOTOR DE DETECÇÃO RÁPIDA (MEDIAPIPE) ---
        # Muito mais leve que o Dlib/HOG
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detector = self.mp_face_detection.FaceDetection(
            model_selection=0, # 0 para rostos a menos de 2m (Webcam)
            min_detection_confidence=0.6
        )
        
        self._load_memory()

    def _load_memory(self):
        """Carrega biometria com tratamento de erro robusto."""
        if not os.path.exists(MEMORY_PATH):
            try:
                os.makedirs(MEMORY_PATH)
            except: pass
            return

        files = [f for f in os.listdir(MEMORY_PATH) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
        log.info(f"📸 Carregando biometria de {len(files)} pessoas...")

        for file in files:
            name = os.path.splitext(file)[0].replace("_", " ").title()
            path = os.path.join(MEMORY_PATH, file)
            
            try:
                # Carregamento seguro (OpenCV -> RGB -> Contiguous)
                img = cv2.imread(path)
                if img is None: continue
                
                rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                rgb_img = np.ascontiguousarray(rgb_img, dtype=np.uint8)

                # Para aprender, ainda usamos o Dlib padrão pois é feito uma única vez no boot
                encodings = face_recognition.face_encodings(rgb_img)
                
                if encodings:
                    self.known_encodings.append(encodings[0])
                    self.known_names.append(name)
                    log.info(f"✅ Biometria: {name}")
                else:
                    log.warning(f"⚠️ Rosto não legível: {file}")
                    
            except Exception as e:
                log.error(f"Erro em {file}: {e}")

    def identify(self, frame):
        """
        1. Usa MediaPipe para achar o rosto (RÁPIDO).
        2. Usa FaceRecognition para saber quem é (PRECISO).
        Retorna: Lista de dicionários [{'nome': str, 'bbox': (x, y, w, h)}]
        """
        if not self.known_encodings:
            return []

        h, w, _ = frame.shape
        face_locations_dlib = [] # Formato (top, right, bottom, left)
        resultados = [] # Lista formatada para o Tracker

        # 1. DETECÇÃO RÁPIDA (MediaPipe)
        # Converte para RGB para o MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False # Pequena otimização
        results = self.face_detector.process(rgb_frame)
        rgb_frame.flags.writeable = True

        if results.detections:
            for detection in results.detections:
                # Extrai Bounding Box do MediaPipe
                bboxC = detection.location_data.relative_bounding_box
                
                # Converte coordenadas relativas (0.0-1.0) para pixels
                left = int(bboxC.xmin * w)
                top = int(bboxC.ymin * h)
                width = int(bboxC.width * w)
                height = int(bboxC.height * h)

                # Margem de segurança (o MediaPipe detecta muito justo, o Dlib precisa de testa/queixo)
                margin_x = int(width * 0.1)
                margin_y = int(height * 0.15)
                
                top = max(0, top - margin_y)
                bottom = min(h, top + height + margin_y * 2)
                left = max(0, left - margin_x)
                right = min(w, left + width + margin_x * 2)

                # Guarda para o passo de reconhecimento
                face_locations_dlib.append((top, right, bottom, left))

        # Se não achou rosto, sai cedo (poupa CPU)
        if not face_locations_dlib:
            return []

        # 2. IDENTIFICAÇÃO (Face Recognition)
        # Passamos as localizações que o MediaPipe achou. 
        # Isso faz o face_recognition PULAR a parte pesada de procurar o rosto.
        try:
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations_dlib)

            for (top, right, bottom, left), encoding in zip(face_locations_dlib, face_encodings):
                matches = face_recognition.compare_faces(self.known_encodings, encoding, tolerance=TOLERANCE)
                name = "Desconhecido"
                
                face_distances = face_recognition.face_distance(self.known_encodings, encoding)
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = self.known_names[best_match_index]

                # --- NOVO: Prepara as coordenadas para o Tracker do OpenCV ---
                largura_box = right - left
                altura_box = bottom - top
                bbox_tracker = (left, top, largura_box, altura_box)
                
                resultados.append({
                    "nome": name,
                    "bbox": bbox_tracker
                })

            return resultados

        except Exception as e:
            log.error(f"Erro no reconhecimento: {e}")
            return []