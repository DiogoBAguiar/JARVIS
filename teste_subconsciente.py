import os
import sys
import time
import logging
import json

# Adiciona raiz ao path
sys.path.append(os.getcwd())

from jarvis_system.hipocampo.subconsciente import Subconsciente
from jarvis_system.hipocampo.reflexos import HipocampoReflexos

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("TESTE")

# ARQUIVOS ISOLADOS PARA O TESTE
LOG_TESTE = "logs/teste_isolado.log"
INTUICAO_TESTE = "jarvis_system/data/intuicao_teste.json"

def limpar_ambiente():
    if os.path.exists(LOG_TESTE): os.remove(LOG_TESTE)
    if os.path.exists(INTUICAO_TESTE): os.remove(INTUICAO_TESTE)
    logger.info("🧹 Ambiente de teste limpo.")

def gerar_logs_controlados():
    logger.info("💉 Injetando cenário de teste isolado...")
    os.makedirs("logs", exist_ok=True)
    
    with open(LOG_TESTE, "w", encoding="utf-8") as f:
        # Cenário: 3 falhas idênticas
        for _ in range(3):
            f.write("2026-01-15 10:00:00 - [INFO] - CORTEX_FRONTAL - 🤔 Processando: 'barulho de ventilador'\n")
            f.write("2026-01-15 10:00:01 - [INFO] - CORTEX_BRAIN - 🧠 Pensamento: 1.0s (sem ação)\n")
            f.write("\n")
            
        f.flush()
        os.fsync(f.fileno())

def testar():
    limpar_ambiente()
    gerar_logs_controlados()
    
    # 1. Instancia o Subconsciente apontando para os arquivos de teste
    sub = Subconsciente(log_path=LOG_TESTE, memory_path=INTUICAO_TESTE)
    sub.sonhar()
    
    # 2. Verifica se o arquivo foi criado
    if not os.path.exists(INTUICAO_TESTE):
        logger.error("❌ ERRO: Arquivo de intuição não foi gerado!")
        return

    # 3. Teste Manual do Reflexo (Simulando a Classe)
    # Como a classe Reflexos carrega o caminho padrão hardcoded, vamos ler o JSON manualmente 
    # para validar o teste sem precisar alterar o código do Reflexos só para isso.
    with open(INTUICAO_TESTE, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    bloqueados = dados.get("ruido_ignorado", [])
    
    print("-" * 40)
    print(f"MEMÓRIA GERADA: {bloqueados}")
    
    if "barulho de ventilador" in bloqueados:
        logger.info("✅ SUCESSO TOTAL! 'barulho de ventilador' foi aprendido como ruído.")
        
        # Teste final: Injetando no Reflexos real (Hack temporário de path)
        reflexos = HipocampoReflexos()
        # Força o reflexo a olhar para nossa memória de teste
        reflexos.ignored_phrases = bloqueados 
        
        _, ignorar = reflexos.processar_reflexo("barulho de ventilador")
        if ignorar:
            logger.info("🛡️  O módulo Reflexos bloqueou corretamente.")
    else:
        logger.error("❌ FALHA! A frase não entrou na lista negra.")
    print("-" * 40)

    # Limpeza final
    # if os.path.exists(LOG_TESTE): os.remove(LOG_TESTE)
    # if os.path.exists(INTUICAO_TESTE): os.remove(INTUICAO_TESTE)

if __name__ == "__main__":
    testar()