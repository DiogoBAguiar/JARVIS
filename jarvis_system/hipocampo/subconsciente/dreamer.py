import os
import logging
from .memory import SubconscienteMemory
from .log_reader import LogReader
from .analyzer import LogAnalyzer

# Configuração de Caminhos Automática
current_dir = os.path.dirname(os.path.abspath(__file__))
# Sobe 3 níveis: subconsciente -> hipocampo -> jarvis_system -> Raiz
root_dir = os.path.abspath(os.path.join(current_dir, '../../..'))

DEFAULT_LOG = os.path.join(root_dir, "logs", "jarvis_system.log")
DEFAULT_MEM = os.path.join(root_dir, "jarvis_system", "data", "intuicao.json")

class Subconsciente:
    def __init__(self, log_path=None, memory_path=None):
        self.log_path = log_path if log_path else DEFAULT_LOG
        self.memory_path = memory_path if memory_path else DEFAULT_MEM
        
        # Injeção de Dependências
        self.memory = SubconscienteMemory(self.memory_path)
        self.reader = LogReader(self.log_path)
        self.analyzer = LogAnalyzer()

    def sonhar(self):
        """Fluxo principal de aprendizado."""
        
        # 1. Extração
        historico = self.reader.ler_logs()
        if not historico: return

        # 2. Carregar contexto atual
        dados_memoria = self.memory.carregar()
        conhecidos = dados_memoria.get("ruido_ignorado", [])

        # 3. Análise (Processamento)
        novos_ruidos = self.analyzer.identificar_ruidos(historico, conhecidos)

        # 4. Persistência (Carga)
        if novos_ruidos:
            qtd_novos = self.memory.atualizar_ruidos(novos_ruidos)
            print(f"🧠 [SUBCONSCIENTE] Sonho concluído.")
            if qtd_novos > 0:
                print(f"   🚫 {qtd_novos} NOVOS bloqueios aprendidos.")
                print(f"   📝 Exemplos: {novos_ruidos[:3]}")
            else:
                print("   💤 Conhecimento consolidado (sem novidades).")
        else:
            print("   💤 Nenhuma nova intuição formada.")