import logging
import time
import sys
import os
from dotenv import load_dotenv

load_dotenv() 

# Configuração de Logs para parecer com o sistema real
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("TEST_SUITE")

# Adiciona o diretório atual ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importa o Agente Singleton
try:
    from jarvis_system.agentes_especialistas.noticias.agent.manager import news_agent
except ImportError as e:
    logger.error(f"Erro de importação: {e}")
    logger.error("Verifique se a estrutura de pastas está correta: jarvis_system/agentes_especialistas/noticias/")
    sys.exit(1)

def run_test(scenario_name, user_input, expected_route="QUALQUER"):
    print(f"\n🔹 [{scenario_name}]")
    print(f"   📥 Input: '{user_input}'")
    
    start_time = time.time()
    
    # 1. Verifica Gatilho (Router)
    if not news_agent.pode_lidar(user_input):
        print(f"   ❌ FALHA: O agente não reconheceu o gatilho.")
        return
    
    # 2. Executa
    try:
        resposta = news_agent.executar(user_input)
        elapsed = time.time() - start_time
        
        print(f"   🧠 Resp: {resposta[:150]}...") # Mostra só o começo pra não poluir
        if len(resposta) > 150: print("   (... continua ...)")
        
        print(f"   ⏱️  Tempo: {elapsed:.2f}s | Status: ✅ PASSOU")
        
    except Exception as e:
        print(f"   ❌ ERRO CRÍTICO: {e}")

def main():
    print("=========================================")
    print("   📰 SUÍTE DE TESTES: NEWS AGENT V1.0   ")
    print("=========================================")
    
    # Pré-check de saúde
    print(f"🔧 Check de Inicialização: {'ONLINE' if news_agent.is_ready else 'OFFLINE'}")
    print(f"🌐 Check de Internet: {'CONECTADO' if news_agent.verificar_saude() else 'DESCONECTADO'}")
    
    if not news_agent.is_ready:
        print("❌ Abortando: Agente não inicializou.")
        return

    # --- CENÁRIO 1: RSS (Deve ser rápido) ---
    # Palavras chave: "futebol", "resumo", "manchetes"
    run_test(
        "01_RSS_FUTEBOL", 
        "Jarvis, quais as novidades do futebol?", 
        expected_route="RSS"
    )

    # --- CENÁRIO 2: RSS (Tecnologia) ---
    # Palavras chave: "tech", "tecnologia"
    run_test(
        "02_RSS_TECH", 
        "Me dê um resumo de tecnologia",
        expected_route="RSS"
    )

    # --- CENÁRIO 3: BUSCA WEB (Deve demorar um pouco mais) ---
    # Tópico específico que não está nos RSS padrões
    run_test(
        "03_BUSCA_SPECIFICA", 
        "Jarvis, o que a OpenAI lançou recentemente?",
        expected_route="BUSCA"
    )

    # --- CENÁRIO 4: BUSCA WEB (Cripto Específico) ---
    # Embora tenha RSS de cripto, perguntas de "preço" ou "motivo" costumam cair na busca
    run_test(
        "04_BUSCA_CRIPTO", 
        "Por que o preço do bitcoin variou hoje?",
        expected_route="BUSCA"
    )

    print("\n=========================================")
    print("   🏁 FIM DA SIMULAÇÃO")
    print("=========================================")

if __name__ == "__main__":
    main()