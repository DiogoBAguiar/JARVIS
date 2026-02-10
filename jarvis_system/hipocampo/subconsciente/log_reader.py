import os
import re
import logging
from datetime import datetime

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
                # Ler tudo para a memória é rápido (<1MB para 15k linhas)
                linhas = f.readlines()
        except Exception as e:
            self.logger.error(f"Erro de leitura: {e}")
            return []

        # OTIMIZAÇÃO: Define a data de hoje para filtrar (Formato YYYY-MM-DD)
        hoje = datetime.now().strftime("%Y-%m-%d")
        
        print(f"📅 [SUBCONSCIENTE] Filtrando logs por data: {hoje}")
        
        historico = []
        total_linhas = len(linhas)
        linhas_processadas = 0

        for i, linha in enumerate(linhas):
            # FILTRO DE ALTA VELOCIDADE:
            # Se a linha não começar com a data de hoje, pula imediatamente.
            # Isso evita rodar Regex em 15.000 linhas antigas.
            if not linha.startswith(hoje):
                continue

            linhas_processadas += 1
            
            # Só executa a regex pesada nas linhas de hoje
            match = self.regex_input.search(linha)
            if match:
                frase = match.group(1).lower().strip()
                if not frase: continue
                
                status = "falha"
                # Janela de look-ahead (8 linhas) para ver se a ação teve sucesso
                for j in range(1, 9):
                    if i + j >= total_linhas: break
                    if self.regex_sucesso.search(linhas[i+j]):
                        status = "sucesso"
                        break
                
                historico.append({"frase": frase, "status": status})
        
        print(f"💤 [SUBCONSCIENTE] {len(linhas)} linhas no total. {linhas_processadas} analisadas (Hoje).")
        return historico