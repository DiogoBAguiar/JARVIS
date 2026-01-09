import os
import sys

# Garante que a raiz do projeto esteja no path
sys.path.append(os.getcwd())

from jarvis_system.hipocampo.memoria import memoria

def jarvis_pergunta(pergunta):
    print(f"\n👤 Usuário: {pergunta}")
    
    # 1. Realiza a busca semântica
    # O método 'relembrar' agora retorna uma lista de strings formatadas
    memorias = memoria.relembrar(pergunta, limite=3)
    
    if memorias:
        # Pega a primeira (mais relevante) para a resposta principal
        resposta_principal = memorias[0].replace("- ", "")
        print(f"🤖 J.A.R.V.I.S: Baseado nos registros, {resposta_principal}")
        
        if len(memorias) > 1:
            print("\n📚 Outras correlações encontradas na memória:")
            for i, m in enumerate(memorias[1:], 1):
                print(f"   {i}. {m.replace('- ', '')}")
    else:
        print("🤖 J.A.R.V.I.S: Senhor, não localizei nenhuma informação correlacionada nos meus bancos de dados.")

def iniciar_teste():
    # Verifica conexão ativa
    if not memoria._is_connected:
        memoria._conectar()

    print("\n" + "="*50)
    print("🧠 CONSOLE DE RECUPERAÇÃO SEMÂNTICA - J.A.R.V.I.S")
    print("="*50)
    print(f"Status: {memoria.status()}")
    print("Digite suas perguntas ou 'sair' para encerrar.")

    while True:
        prompt = input("\nPergunta: ")
        if prompt.lower() in ['sair', 'exit', 'quit']:
            print("🤖 J.A.R.V.I.S: Encerrando consulta. Até logo, Senhor.")
            break
        
        if not prompt.strip():
            continue
            
        jarvis_pergunta(prompt)

if __name__ == "__main__":
    iniciar_teste()