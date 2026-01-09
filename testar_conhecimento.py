import os
import sys

# Adiciona raiz ao path
sys.path.append(os.getcwd())

from jarvis_system.hipocampo.memoria import memoria

def jarvis_pergunta(pergunta):
    print(f"\n👤 Usuário: {pergunta}")
    
    # Tentamos usar o método de busca da coleção do ChromaDB diretamente
    # para garantir que não haverá erro de atributo
    try:
        # Busca semântica: transforma a pergunta em vetor e compara no banco
        resultados = memoria.collection.query(
            query_texts=[pergunta],
            n_results=3
        )
        
        if resultados and resultados['documents'][0]:
            print(f"🤖 J.A.R.V.I.S: Baseado na minha memória, {resultados['documents'][0][0]}")
            
            print("\n📚 Outras correspondências próximas:")
            for i, doc in enumerate(resultados['documents'][0][1:], 1):
                print(f"   {i}. {doc}")
        else:
            print("🤖 J.A.R.V.I.S: Senhor, não encontrei registros sobre isso.")
            
    except Exception as e:
        print(f"❌ Erro na consulta: {e}")

def iniciar_teste():
    if memoria.collection is None:
        memoria._conectar()

    print("=== TESTE DE CONHECIMENTO DO J.A.R.V.I.S ===")
    print("Digite suas perguntas ou 'sair' para encerrar.")

    while True:
        prompt = input("\nPergunta: ")
        if prompt.lower() in ['sair', 'exit', 'quit']:
            break
        jarvis_pergunta(prompt)

if __name__ == "__main__":
    iniciar_teste()