import dlib
import torch

print("====================================")
print("🔍 RELATÓRIO DE HARDWARE DO J.A.R.V.I.S.")
print("====================================")

# Teste do Dlib (Reconhecimento Facial)
if dlib.DLIB_USE_CUDA:
    print("✅ DLIB: GPU CUDA ATIVADA! (Reconhecimento Facial a jato)")
else:
    print("❌ DLIB: Rodando na CPU (Ainda não achou a GPU).")

# Teste do PyTorch (Futuro YOLO)
if torch.cuda.is_available():
    print(f"✅ PYTORCH: GPU CUDA ATIVADA! Placa Encontrada: {torch.cuda.get_device_name(0)}")
else:
    print("❌ PYTORCH: Rodando na CPU.")