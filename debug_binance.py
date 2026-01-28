import logging
import sys
import os
import time
from colorama import init, Fore, Style
from dotenv import load_dotenv # Importante

# Inicializa cores
init(autoreset=True)

# --- 0. DIAGNÓSTICO DE AMBIENTE (CRUCIAL) ---
print(f"{Fore.BLUE}{'='*60}")
print(f" 🔧 DIAGNÓSTICO DE AMBIENTE (.ENV)")
print(f"{'='*60}{Style.RESET_ALL}")

# 1. Tenta carregar o .env forçando o caminho absoluto da raiz
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '.env')

print(f"📂 Procurando .env em: {env_path}")

if os.path.exists(env_path):
    print(f"{Fore.GREEN}✅ Arquivo .env encontrado!{Style.RESET_ALL}")
    load_dotenv(env_path, override=True) # Força recarga
else:
    print(f"{Fore.RED}❌ Arquivo .env NÃO encontrado neste caminho.{Style.RESET_ALL}")

# 2. Verifica se a chave específica existe (sem mostrar ela toda por segurança)
groq_key = os.getenv("GROQ_API_KEY")
if groq_key:
    masked_key = groq_key[:5] + "..." + groq_key[-4:]
    print(f"{Fore.GREEN}✅ GROQ_API_KEY detectada: {masked_key}{Style.RESET_ALL}")
else:
    print(f"{Fore.RED}❌ GROQ_API_KEY não encontrada nas variáveis de ambiente!{Style.RESET_ALL}")
    print("   -> Verifique se no arquivo .env está escrito exatamente: GROQ_API_KEY=gsk_...")

print("-" * 60)

# --- 1. CONFIGURAÇÃO DE LOGGING ---
logging.basicConfig(
    level=logging.INFO, # Mudei para INFO para limpar um pouco o output do HTTP
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("DEBUG_TOOL")

# Adiciona diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_debug():
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f" 🕵️  DEBUG ISOLADO: CENÁRIO BINANCE")
    print(f"{'='*60}{Style.RESET_ALL}")

    # --- 2. IMPORTAÇÃO ---
    print(f"{Fore.YELLOW}⏳ Importando Agente de Notícias...{Style.RESET_ALL}")
    try:
        from jarvis_system.agentes_especialistas.noticias.agent.manager import news_agent
        print(f"{Fore.GREEN}✅ Importação com sucesso.{Style.RESET_ALL}")
    except ImportError as e:
        print(f"{Fore.RED}❌ Erro Crítico na Importação: {e}{Style.RESET_ALL}")
        sys.exit(1)

    # Input que deu erro
    user_input = "Novidades da Binance"

    print(f"\n{Fore.CYAN}📥 Input:{Style.RESET_ALL} '{user_input}'")
    print(f"{Fore.YELLOW}🚀 Iniciando execução...{Style.RESET_ALL}")
    
    start_time = time.time()

    try:
        # --- 3. EXECUÇÃO ---
        aceita = news_agent.pode_lidar(user_input)
        
        if aceita:
            resposta = news_agent.executar(user_input)
            elapsed = time.time() - start_time
            
            print(f"\n{Fore.GREEN}✅ CONCLUÍDO EM {elapsed:.2f}s{Style.RESET_ALL}")
            print(f"\n{Fore.CYAN}--- RESPOSTA FINAL DO AGENTE ---{Style.RESET_ALL}")
            print(resposta)
            print(f"{Fore.CYAN}--------------------------------{Style.RESET_ALL}")
            
            # Validação do Mock
            if "esporte" in resposta.lower() and "binance" not in resposta.lower():
                print(f"\n{Fore.RED}🚨 ALERTA: O sistema ainda está alucinando sobre ESPORTES.{Style.RESET_ALL}")
                print("Isso confirma que ele está caindo no 'Mock' padrão.")
            elif ".html" in resposta:
                print(f"\n{Fore.BLUE}📄 ARQUIVO HTML GERADO.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ Gatekeeper rejeitou o termo.{Style.RESET_ALL}")

    except Exception as e:
        print(f"\n{Fore.RED}🔥 CRASH:{Style.RESET_ALL} {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_debug()