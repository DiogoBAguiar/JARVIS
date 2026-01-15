import os
import re
import logging

class LogReader:
    def __init__(self, log_path):
        self.log_path = log_path
        self.logger = logging.getLogger("SUBCONSCIENTE_READER")
        
        # Regex Pré-compilada para performance
        self.regex_input = re.compile(r"Processando:\s*['\"](.*?)['\"]")
        self.regex_sucesso = re.compile(r"Agente acionado|Delegando para|Iniciando subsistema")

    def ler_logs(self):
        if not os.path.exists(self.log_path):
            self.logger.warning(f"Log não encontrado: {self.log_path}")
            return []

        try:
            with open(self.log_path, 'r', encoding='utf-8') as f:
                linhas = f.readlines()
        except Exception as e:
            self.logger.error(f"Erro de leitura: {e}")
            return []

        print(f"💤 [SUBCONSCIENTE] Lendo {len(linhas)} linhas do diário...")
        
        historico = []
        total_linhas = len(linhas)

        for i, linha in enumerate(linhas):
            match = self.regex_input.search(linha)
            if match:
                frase = match.group(1).lower().strip()
                if not frase: continue
                
                status = "falha"
                # Janela de look-ahead (8 linhas)
                for j in range(1, 9):
                    if i + j >= total_linhas: break
                    if self.regex_sucesso.search(linhas[i+j]):
                        status = "sucesso"
                        break
                
                historico.append({"frase": frase, "status": status})
                
        return historico