import sys
import os
import time
import logging

# Configuração de Logs para o Teste
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("TEST_SIMULATOR")

# 1. Garante que o diretório atual é a raiz do projeto
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# 2. Importa o Kernel
try:
    from jarvis_system.main.core import kernel
except ImportError:
    logger.critical("❌ Erro: Não foi possível importar o Kernel. Verifique se está na raiz do projeto.")
    sys.exit(1)

# --- BATERIA DE TESTES (CORRIGIDA COM WAKE WORD) ---
# Adicionamos "Jarvis, " antes de cada comando para abrir a janela de atenção.
TEST_CASES = [
    # Categoria: Spotify (Alta Prioridade)
    {"input": "Jarvis, Tocar Coldplay", "desc": "Comando Perfeito (Artista)"},
    {"input": "Jarvis, tocar metalica", "desc": "Erro Ortográfico (Metalica -> Metallica)"},
    {"input": "Jarvis, bota um som de matue ai", "desc": "Gíria / Contexto Informal"},
    {"input": "Jarvis, reproduzir musica bohemian rhapsody", "desc": "Comando Explícito (Música)"},
    {"input": "Jarvis, ouvir playlist foco", "desc": "Playlist"},
    
    # Categoria: Controles de Mídia
    {"input": "Jarvis, pausar", "desc": "Comando Único"},
    {"input": "Jarvis, aumenta o volume", "desc": "Variação Verbal"},
    {"input": "Jarvis, proxima", "desc": "Navegação"},
    
    # Categoria: Sistema
    {"input": "Jarvis, abrir spotify", "desc": "Abrir App"},
    {"input": "Jarvis, calculadora", "desc": "Nome Curto de App"},
    
    # Categoria: Conversa / Outros
    {"input": "Jarvis, qual o sentido da vida", "desc": "Pergunta Filosófica (LLM Puro)"},
    
    # Categoria: Testes de Robustez
    {"input": "Jarvis, tocaaarrrr linkin park", "desc": "Ruído extremo de teclado"},
    {"input": "", "desc": "Input Vazio (Deve ser ignorado)"},
]

def run_tests():
    print("\n=========================================")
    print("   🧪 INICIANDO SIMULAÇÃO DE CÓRTEX V2.1 ")
    print("   📢 Modo: Comandos com Wake Word       ")
    print("=========================================\n")

    logger.info("⚙️  Inicializando Kernel (Bootstrap)...")
    kernel.bootstrap()
    
    # Pequena pausa para garantir que os módulos assíncronos subiram
    time.sleep(2)
    
    sucessos = 0
    falhas = 0
    start_total = time.time()

    for i, case in enumerate(TEST_CASES):
        texto = case["input"]
        desc = case["desc"]
        
        print(f"\n🔹 [Teste {i+1}/{len(TEST_CASES)}]: {desc}")
        print(f"   📥 Input: '{texto}'")
        
        try:
            t0 = time.time()
            
            # Chama o método que criamos no Orchestrator
            if kernel.brain:
                # O brain.processar() agora deve lidar com "Jarvis, ..."
                resposta = kernel.brain.processar(texto)
            else:
                resposta = "ERRO: Cérebro não inicializado."
                
            dt = time.time() - t0
            
            print(f"   🧠 Resposta: {resposta}")
            print(f"   ⏱️  Tempo: {dt:.2f}s")
            
            # Validação do Sucesso
            if texto == "":
                # Se o input for vazio, a resposta DEVE ser vazia ou indicação de erro tratado
                if not resposta or "Sem resposta" in resposta:
                    sucessos += 1
                else:
                    print("   ⚠️  Falha: Respondeu algo para input vazio.")
                    falhas += 1
            else:
                # Se for comando real, esperamos uma resposta diferente de "Sem resposta vocal."
                if resposta and "Sem resposta vocal" not in resposta and "ERRO" not in resposta:
                    sucessos += 1
                else:
                    print("   ⚠️  Atenção: Jarvis não respondeu ou ignorou o comando.")
                    falhas += 1
                
        except Exception as e:
            print(f"   ❌ EXCEÇÃO FATAL: {e}")
            falhas += 1
            
        time.sleep(1.0) # Pausa maior para não atropelar o log

    print("\n=========================================")
    print(f"   🏁 RELATÓRIO FINAL")
    print(f"   ✅ Sucessos: {sucessos}")
    print(f"   ❌ Falhas: {falhas}")
    print(f"   🕒 Tempo Total: {time.time() - start_total:.2f}s")
    print("=========================================")

    kernel.shutdown()

if __name__ == "__main__":
    run_tests()