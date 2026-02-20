import mediapipe as mp
import math

class HandSensor:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )

    def calcular_distancia(self, p1, p2):
        """Calcula a distância euclidiana entre dois pontos 3D ou 2D."""
        return math.hypot(p2.x - p1.x, p2.y - p1.y)

    def processar(self, rgb_frame):
        results = self.hands.process(rgb_frame)
        if not results.multi_hand_landmarks:
            return None
        
        landmarks = results.multi_hand_landmarks[0].landmark
        
        # 1. ESTADO DOS DEDOS (0 = Baixado, 1 = Levantado)
        fingers = []
        
        # Lógica especial para o POLEGAR (compara horizontalidade com a base do indicador)
        # Se o x da ponta (4) for maior/menor que o x da junta (2) dependendo da mão
        if landmarks[4].x < landmarks[3].x:
            fingers.append(1)
        else:
            fingers.append(0)

        # Lógica para os outros 4 DEDOS (Ponta vs Articulação anterior)
        # [Indicador, Médio, Anelar, Mindinho]
        for tip, pip in [(8, 6), (12, 10), (16, 14), (20, 18)]:
            if landmarks[tip].y < landmarks[pip].y:
                fingers.append(1)
            else:
                fingers.append(0)

        total_levantados = sum(fingers)
        indicador_medio_juntos = self.calcular_distancia(landmarks[8], landmarks[12]) < 0.05
        dist_pinca = self.calcular_distancia(landmarks[4], landmarks[8])

        # ---------------------------------------------------------
        # 2. DICIONÁRIO DE GESTOS (Prioridade por complexidade)
        # ---------------------------------------------------------

        # GESTO: OK (Pinça entre polegar e indicador + outros 3 levantados)
        if dist_pinca < 0.04 and fingers[2:] == [1, 1, 1]:
            return "OK"

        # GESTO: ROCK (Polegar, Indicador e Mindinho levantados)
        if fingers == [1, 1, 0, 0, 1]:
            return "ROCK"

        # GESTO: VITÓRIA / PAZ (Apenas indicador e médio levantados)
        if fingers == [0, 1, 1, 0, 0]:
            return "VITORIA"

        # GESTO: LEGAL (Apenas polegar levantado)
        if fingers == [1, 0, 0, 0, 0]:
            return "LEGAL"

        # GESTO: PINÇA (Geral)
        if dist_pinca < 0.04:
            return "PINCA"

        # RECONHECIMENTO NUMÉRICO (1 a 5)
        if total_levantados == 5:
            return "CINCO / PARE"
        elif fingers == [0, 1, 1, 1, 1]:
            return "QUATRO"
        elif fingers == [0, 1, 1, 1, 0]:
            return "TRES"
        elif fingers == [0, 1, 1, 0, 0]: # Caso não entre no 'Vitoria'
            return "DOIS"
        elif fingers == [0, 1, 0, 0, 0]:
            return "UM / APONTAR"
        elif total_levantados == 0:
            return "PUNHO FECHADO"

        return "NEUTRO"