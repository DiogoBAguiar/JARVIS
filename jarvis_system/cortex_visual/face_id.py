import os
import cv2
import face_recognition
import numpy as np
from jarvis_system.cortex_frontal.observability import JarvisLogger
from .config import MEMORY_PATH, TOLERANCE

log = JarvisLogger("VISUAL_FACEID")

class BiometricSystem:
    def __init__(self):
        self.known_encodings = []
        self.known_names = []
        self._load_memory()

    def _load_memory(self):
        """Carrega todas as fotos da pasta memory/ e aprende os rostos."""
        if not os.path.exists(MEMORY_PATH):
            os.makedirs(MEMORY_PATH)
            log.warning(f"Pasta de memória visual criada vazia: {MEMORY_PATH}")
            return

        files = [f for f in os.listdir(MEMORY_PATH) if f.endswith(('.jpg', '.png'))]
        log.info(f"📸 Carregando biometria de {len(files)} pessoas...")

        for file in files:
            name = os.path.splitext(file)[0].replace("_", " ").title()
            path = os.path.join(MEMORY_PATH, file)
            
            try:
                img = face_recognition.load_image_file(path)
                encodings = face_recognition.face_encodings(img)
                
                if encodings:
                    self.known_encodings.append(encodings[0])
                    self.known_names.append(name)
                    log.info(f"✅ Biometria aprendida: {name}")
                else:
                    log.warning(f"⚠️ Nenhum rosto encontrado em {file}")
            except Exception as e:
                log.error(f"Erro ao ler {file}: {e}")

    def identify(self, frame):
        """
        Recebe um frame BGR (OpenCV), converte e busca rostos.
        Retorna: Lista de nomes encontrados ['Diogo', 'Desconhecido']
        """
        if not self.known_encodings:
            return []

        # Otimização: Reduz imagem para 1/4 para processar 4x mais rápido
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        
        # Converte BGR (OpenCV) -> RGB (Face Recognition)
        rgb_small_frame = np.ascontiguousarray(small_frame[:, :, ::-1])

        # Detecta rostos
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        found_names = []
        
        for encoding in face_encodings:
            matches = face_recognition.compare_faces(self.known_encodings, encoding, tolerance=TOLERANCE)
            name = "Desconhecido"

            # Se houver match, usa a distância matemática para achar o "melhor match"
            face_distances = face_recognition.face_distance(self.known_encodings, encoding)
            best_match_index = np.argmin(face_distances)
            
            if matches[best_match_index]:
                name = self.known_names[best_match_index]

            found_names.append(name)
            
        return found_names