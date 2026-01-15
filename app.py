import sys
import os
import uvicorn

# 1. Garante que o diretório atual é a raiz do projeto
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# 2. Importa o APP diretamente (Carrega o Kernel e o FastAPI na memória)
from jarvis_system.main.api import app

def main():
    print("=========================================")
    print("   🚀 J.A.R.V.I.S. SYSTEM ONLINE (V3)   ")
    print("   🌐 Modo: API Server + Voice Engine    ")
    print("=========================================")
    
    # Mude port=8000 para port=8001
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")

if __name__ == "__main__":
    main()