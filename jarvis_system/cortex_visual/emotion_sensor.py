import mediapipe as mp
import math

class EmotionSensor:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )

    def calcular_distancia(self, p1, p2):
        return math.hypot(p2.x - p1.x, p2.y - p1.y)

    def processar(self, rgb_frame):
        results = self.face_mesh.process(rgb_frame)
        if not results.multi_face_landmarks:
            return None

        landmarks = results.multi_face_landmarks[0].landmark

        # Pontos âncora do rosto
        olho_esq = landmarks[33]
        olho_dir = landmarks[263]
        canto_esq_boca = landmarks[61]
        canto_dir_boca = landmarks[291]
        labio_sup = landmarks[13]
        labio_inf = landmarks[14]

        # Usamos a distância entre os olhos como "régua" para saber se você está perto ou longe da câmara
        distancia_olhos = self.calcular_distancia(olho_esq, olho_dir)
        if distancia_olhos == 0: return "NEUTRO"

        largura_boca = self.calcular_distancia(canto_esq_boca, canto_dir_boca)
        abertura_boca = self.calcular_distancia(labio_sup, labio_inf)

        # Proporções geométricas
        razao_sorriso = largura_boca / distancia_olhos
        razao_abertura = abertura_boca / distancia_olhos

        # Lógica de Emoção
        if razao_sorriso > 0.95:  # Boca esticou horizontalmente
            if razao_abertura > 0.15:
                return "SORRISO ABERTO"
            return "SORRISO"
        elif razao_abertura > 0.35 and razao_sorriso < 0.85: # Boca abriu muito em "O"
            return "SURPRESA"
            
        return "NEUTRO"