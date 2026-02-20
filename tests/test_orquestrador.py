import sys
import os

# Adiciona a raiz do projeto ao caminho do Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jarvis_system.cortex_frontal.orchestrator.orchestrator import Orchestrator
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos

# 1. CRIAMOS UM "ALTO-FALANTE FALSO"
# Tudo o que o Orquestrador mandar o Jarvis falar, nós capturamos aqui e imprimimos.
def alto_falante_falso(evento: Evento):
    texto = evento.dados.get("texto", "")
    print(f"\n🔊 [RESPOSTA DO JARVIS]: '{texto}'\n")

def testar_roteamento():
    print("🚀 Iniciando Ambiente de Teste do Orquestrador...\n")
    
    # Inscrevemos o nosso alto-falante falso no barramento
    bus.inscrever(Eventos.FALAR, alto_falante_falso)
    
    try:
        # 2. INSTANCIAMOS O CÉREBRO
        print("🧠 A carregar Córtex Frontal...")
        orquestrador = Orchestrator()
        
        # 3. BATERIA DE TESTES (Inputs Simulados)
        frases_teste = [
            "jarvis tocar coldplay",
            "jarvis abrir bloco de notas",
            "jarvis qual é o sentido da vida?"
        ]
        
        for frase in frases_teste:
            print("="*60)
            print(f"🎤 [OUVIDO SIMULADO]: {frase}")
            print("="*60)
            
            # Criamos um evento falso idêntico ao que o seu ouvidoBiologico gera
            evento_falso = Evento(Eventos.FALA_RECONHECIDA, {"texto": frase})
            
            # Injetamos diretamente no Orquestrador
            orquestrador.process_input(evento_falso)
            
    except Exception as e:
        print(f"❌ Erro Crítico durante o teste: {e}")

if __name__ == "__main__":
    testar_roteamento()