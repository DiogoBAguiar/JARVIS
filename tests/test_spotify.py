import sys
import os

# Adiciona a raiz do projeto ao caminho do Python para ele encontrar o jarvis_system
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jarvis_system.agentes_especialistas.spotify.agent.agenteSpotify import AgenteSpotify

def testar_spotify():
    print("🚀 Iniciando Teste Isolado do Agente Spotify...")
    
    try:
        agente = AgenteSpotify()
        comando_teste = "tocar coldplay"
        
        print(f"🎵 A enviar comando: '{comando_teste}'")
        resultado = agente.executar(comando_teste)
        
        print(f"\n✅ Resultado do Agente: {resultado}")
        
    except Exception as e:
        print(f"\n❌ Erro Crítico no Agente: {e}")

if __name__ == "__main__":
    testar_spotify()