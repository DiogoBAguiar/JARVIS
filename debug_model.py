import os

# O caminho que definimos no código
TARGET_PATH = os.path.join("jarvis_system", "area_broca", "model")
ABS_PATH = os.path.abspath(TARGET_PATH)

print(f"--- DIAGNÓSTICO DE CAMINHO ---")
print(f"Procurando modelo em: {TARGET_PATH}")
print(f"Caminho Absoluto:     {ABS_PATH}")

if not os.path.exists(TARGET_PATH):
    print("\n[ERRO CRÍTICO] A pasta NÃO EXISTE.")
else:
    print("\n[OK] A pasta existe. Listando conteúdo:")
    arquivos = os.listdir(TARGET_PATH)
    for f in arquivos:
        if os.path.isdir(os.path.join(TARGET_PATH, f)):
            print(f"   [DIR]  {f}  <-- SE ISSO APARECER, OS ARQUIVOS ESTÃO AQUI DENTRO?")
        else:
            print(f"   [FILE] {f}")

    # Verificação de arquivos obrigatórios do Vosk
    essenciais = ["final.mdl", "conf", "Gr.fst"]
    faltantes = [f for f in essenciais if f not in arquivos]
    
    if faltantes:
        print(f"\n[FALHA] Faltam arquivos essenciais na raiz da pasta model: {faltantes}")
        print("SOLUÇÃO: Mova os arquivos de dentro da subpasta para cá.")
    else:
        print("\n[SUCESSO] A estrutura parece correta. O problema pode ser permissão ou arquivo corrompido.")