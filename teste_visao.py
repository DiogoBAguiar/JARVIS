import pyautogui
import os
import time

# Caminho exato da imagem
img_path = os.path.join(os.getcwd(), "img", "play_spotify.png")

print("--- DIAGNÓSTICO DE VISÃO ---")
print(f"📂 Procurando imagem em: {img_path}")

if not os.path.exists(img_path):
    print("❌ ERRO CRÍTICO: O arquivo 'play_spotify.png' NÃO está na pasta img!")
    exit()

print("👀 Olhe para o Spotify agora. Vou procurar o botão em 3 segundos...")
time.sleep(3)

try:
    # Reduzi a confiança para 0.7 (aceita 70% de semelhança)
    # Grayscale=False é importante para diferenciar o Verde do Cinza
    location = pyautogui.locateCenterOnScreen(img_path, confidence=0.7)
    
    if location:
        print(f"✅ ACHEI! Coordenadas: {location}")
        print("Movendo mouse para lá agora...")
        pyautogui.moveTo(location)
    else:
        print("❌ NÃO ACHEI. O Python não está vendo o botão.")
        print("Dicas:")
        print("1. Tire o print SEM o mouse em cima do botão.")
        print("2. O print deve pegar SÓ a bolinha verde, sem fundo cinza.")
        
except Exception as e:
    print(f"❌ ERRO TÉCNICO: {e}")
    print("Você instalou o opencv? (pip install opencv-python)")