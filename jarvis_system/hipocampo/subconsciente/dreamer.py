import os
import logging
import random
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
    """
    Processo de fundo: Analisa logs passados para aprender novos padrões de ruído.
    """
    def __init__(self, log_path=None, memory_path=None):
        self.log_path = log_path if log_path else DEFAULT_LOG
        self.memory_path = memory_path if memory_path else DEFAULT_MEM
        
        # Injeção de Dependências
        self.memory = SubconscienteMemory(self.memory_path)
        self.reader = LogReader(self.log_path)
        self.analyzer = LogAnalyzer()

    def sonhar(self):
        """Fluxo principal de aprendizado (Offline)."""
        
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

class DayDreamer:
    """
    Processo de Tempo Real: Curiosidade e Interação.
    Responsável por gerar perguntas de follow-up SEM QUEBRAR COMANDOS TÉCNICOS.
    """
    def __init__(self):
        self.logger = logging.getLogger("SUBCONSCIENTE_DREAMER")
        self.perguntas_genericas = [
            "Posso ajudar em algo mais?",
            "Há mais alguma tarefa pendente?",
            "O que mais manda, chefe?",
            "Deseja configurar algo mais?",
            "Como posso ser útil agora?"
        ]

    def gerar_pergunta(self, input_usuario: str, resposta_atual: str = "") -> str:
        """
        Decide se deve adicionar uma pergunta.
        
        🛡️ BLINDAGEM DE JSON:
        Se a resposta atual contiver chaves '{ }', retorna vazio para não corromper
        o comando que vai para o Orchestrator.
        """
        
        # 1. PROTEÇÃO CRÍTICA CONTRA JSON
        if "{" in resposta_atual or "}" in resposta_atual:
            return ""
            
        # 2. Proteção contra respostas de sistema
        if "sistema" in resposta_atual.lower() and "online" in resposta_atual.lower():
            return ""

        # 3. Fator de Aleatoriedade (30% de chance de falar)
        if random.random() > 0.3:
            return ""

        # 4. Lógica Contextual Simples
        input_lower = input_usuario.lower()
        
        if "música" in input_lower or "tocar" in input_lower:
            return "O volume está adequado?"
        
        if "projeto" in input_lower or "código" in input_lower:
            return "Quer que eu registre isso na memória?"

        # 5. Fallback Genérico
        return random.choice(self.perguntas_genericas)