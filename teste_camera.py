import mediapipe as mp
try:
    print(f"MediaPipe Location: {mp.__file__}")
    test = mp.solutions.face_detection
    print("✅ MediaPipe carregado com sucesso! .solutions disponível.")
except AttributeError:
    print("❌ Erro: mp.solutions ainda não existe.")
except Exception as e:
    print(f"❌ Outro erro: {e}")