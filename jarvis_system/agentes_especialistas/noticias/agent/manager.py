import logging
import socket
# ALTERAÇÃO: Conectando direto ao Cérebro V3 para garantir os recursos novos (PDF, Classificador)
from ..brain.core import NewsBrain
from . import config

logger = logging.getLogger("NEWS_MANAGER")

class NewsAgent:
    """
    Classe Principal do Agente de Notícias (V3).
    Responsável pelo ciclo de vida, verificação de saúde e ponte com o Cérebro.
    """

    def __init__(self):
        self.name = config.AGENT_NAME
        self.triggers = config.TRIGGERS
        self.brain = None # Mudança de Controller para Brain
        self.is_ready = False
        
        # Inicialização Lazy
        self._inicializar()

    def _inicializar(self):
        logger.info(f"📰 Inicializando {self.name} v{config.VERSION}...")
        try:
            # Instancia o Cérebro V3 (que carrega o Search Engine, Reporter e LLM)
            self.brain = NewsBrain()
            self.is_ready = True
            logger.info("✅ Agente de Notícias pronto para operar.")
        except Exception as e:
            logger.error(f"❌ Falha ao inicializar Agente de Notícias: {e}")
            self.is_ready = False

    def verificar_saude(self) -> bool:
        """
        Sensor Vital: Verifica se há internet via Socket (rápido e leve).
        """
        try:
            # Tenta conectar ao DNS do Google (8.8.8.8) na porta 53
            with socket.create_connection(("8.8.8.8", 53), timeout=2):
                return True
        except OSError:
            return False

    def pode_lidar(self, user_input: str) -> bool:
        """
        O Porteiro (Gatekeeper).
        Verifica se a frase contém gatilhos definidos no config.py.
        """
        if not self.triggers: return False
        
        termo = user_input.lower()
        
        # Lógica de verificação
        for gatilho in self.triggers:
            # Verifica se o gatilho existe na frase
            # Ex: "cs" in "resultado do cs" -> True
            if gatilho in termo:
                return True
        return False

    def executar(self, user_input: str) -> str:
        """
        Executa a tarefa.
        Fluxo: Check Internet -> Brain V3 -> Resposta (Texto ou Aviso de PDF)
        """
        # 1. Verifica Inicialização
        if not self.is_ready or not self.brain:
            # Tenta reinicializar caso tenha falhado antes
            self._inicializar()
            if not self.is_ready:
                return "O sistema de notícias está offline no momento, senhor."

        # 2. Sentir (Check Vitals)
        if not self.verificar_saude():
            return "Senhor, detectei uma falha na conexão com a rede mundial. Não consigo atualizar as notícias agora."

        # 3. Agir (Delegar ao Cérebro V3)
        try:
            # Chama o método processar_solicitacao do core.py atualizado
            return self.brain.processar_solicitacao(user_input)
        except Exception as e:
            logger.error(f"Erro na execução do Brain: {e}")
            return "Tive um problema interno ao processar os dados da imprensa, senhor."

# Singleton para importação fácil no main.py
news_agent = NewsAgent()