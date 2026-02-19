import mediapipe as mp
import cv2

class HandSensor:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7
        )

    def processar(self, rgb_frame):
        results = self.hands.process(rgb_frame)
        if not results.multi_hand_landmarks:
            return None
        
        # Lógica simplificada: Conta dedos para gestos básicos
        landmarks = results.multi_hand_landmarks[0].landmark
        fingers = []
        # Dedos (Indicador ao Mindinho)
        for id in [8, 12, 16, 20]:
            if landmarks[id].y < landmarks[id - 2].y:
                fingers.append(1)
            else:
                fingers.append(0)
        
        total = sum(fingers)
        if total == 4: return "PARE"
        if total == 0: return "ROCK"
        return "NEUTRO"