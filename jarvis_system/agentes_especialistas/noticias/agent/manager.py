import logging
import socket
from ..controller.news_controller import NewsController
from . import config

logger = logging.getLogger("NEWS_MANAGER")

class NewsAgent:
    """
    Classe Principal do Agente de Notícias.
    Responsável pelo ciclo de vida e verificações de pré-requisitos (Internet).
    """

    def __init__(self):
        self.name = config.AGENT_NAME
        self.triggers = config.TRIGGERS
        self.controller = None
        self.is_ready = False
        
        # Inicialização Lazy (só carrega o cérebro pesado se necessário)
        self._inicializar()

    def _inicializar(self):
        logger.info(f"📰 Inicializando {self.name} v{config.VERSION}...")
        try:
            self.controller = NewsController()
            self.is_ready = True
            logger.info("✅ Agente de Notícias pronto para operar.")
        except Exception as e:
            logger.error(f"❌ Falha ao inicializar Agente de Notícias: {e}")
            self.is_ready = False

    def verificar_saude(self) -> bool:
        """
        Sensor Vital: Verifica se há internet antes de tentar buscar algo.
        Evita erros feios de timeout no meio do processo.
        """
        try:
            # Tenta conectar ao DNS do Google (rápido e leve)
            # O 'with' garante que a conexão fecha sozinha, evitando ResourceWarning
            with socket.create_connection(("8.8.8.8", 53), timeout=3):
                return True
        except OSError:
            logger.warning("⚠️ Agente de Notícias detectou falta de conexão com a Internet.")
            return False

    def pode_lidar(self, user_input: str) -> bool:
        """
        Verifica se a frase contém gatilhos deste agente.
        (Usado pelo Router Principal do Jarvis)
        """
        termo = user_input.lower()
        return any(gatilho in termo for gatilho in self.triggers)

    def executar(self, user_input: str) -> str:
        """
        Executa a tarefa.
        Fluxo: Check Internet -> Controller -> Brain -> Resposta
        """
        if not self.is_ready:
            return "O sistema de notícias não foi inicializado corretamente, senhor."

        # 1. Sentir (Check Vitals)
        if not self.verificar_saude():
            return "Senhor, parece que estamos sem conexão com a internet. Não consigo buscar as notícias agora."

        # 2. Agir (Delegar ao Controller)
        return self.controller.handle_request(user_input)

# Singleton para fácil importação
news_agent = NewsAgent()