import os

def mapear_sistema(diretorio_raiz, arquivo_saida):
    # Pastas para ignorar completamente (não aparecem na lista)
    ignorar_completamente = {
        '.venv', '.git', '__pycache__', '_pycache', 
        'whatsapp_session', 'temp_images', 'relatorios_inteligencia', 'logs' , 'spotify_web_session' , 
    }
    
    # Arquivos específicos para ignorar
    arquivos_ignorar = {'.env', 'projeto_estrutura.txt', 'mapear_projeto.py'}
    
    # Pastas onde queremos mostrar apenas o nome da pasta, mas esconder o conteúdo
    esconder_conteudo_de = {'data'}

    with open(arquivo_saida, 'w', encoding='utf-8') as f:
        f.write(f"ESTRUTURA SIMPLIFICADA DO PROJETO: {os.path.basename(diretorio_raiz)}\n")
        f.write("="*60 + "\n\n")
        
        for raiz, pastas, arquivos in os.walk(diretorio_raiz):
            # Filtra pastas que não devem ser processadas de forma alguma
            pastas[:] = [p for p in pastas if p not in ignorar_completamente]
            
            # Informações da pasta atual
            nome_pasta_atual = os.path.basename(raiz)
            nivel = raiz.replace(diretorio_raiz, '').count(os.sep)
            indentacao = '│   ' * (nivel - 1) + '├── ' if nivel > 0 else ''

            # Escreve o nome da pasta (se não for a raiz)
            if nivel > 0:
                f.write(f"{indentacao}{nome_pasta_atual}/\n")
            else:
                f.write(f". (Raiz)\n")
            
            # Regra para a pasta 'data': mostrar a pasta mas ignorar o que tem dentro
            if nome_pasta_atual in esconder_conteudo_de:
                pastas[:] = [] # Impede o script de entrar em subpastas
                f.write('│   ' * nivel + '└── (Conteúdo Omitido)\n')
                continue # Pula a listagem de arquivos desta pasta

            # Listagem de arquivos
            sub_indentacao = '│   ' * nivel + '└── '
            for arquivo in arquivos:
                if arquivo not in arquivos_ignorar:
                    f.write(f"{sub_indentacao}{arquivo}\n")

if __name__ == "__main__":
    # Garante que estamos mapeando a partir da raiz do projeto
    diretorio_projeto = os.getcwd()
    arquivo_resultado = "projeto_estrutura.txt"
    
    print(f"📊 Mapeando estrutura técnica...")
    mapear_sistema(diretorio_projeto, arquivo_resultado)
    print(f"✅ Arquivo '{arquivo_resultado}' gerado com sucesso.")