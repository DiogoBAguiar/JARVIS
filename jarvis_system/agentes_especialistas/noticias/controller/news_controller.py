import logging
from ..brain.newsBrain import NewsBrain

logger = logging.getLogger("NEWS_CONTROLLER")

class NewsController:
    """
    Controlador Fachada para o Agente de Notícias.
    Mantém o estado e a instância do Cérebro.
    """
    def __init__(self):
        logger.info("🗞️ Inicializando Agente de Notícias...")
        self.brain = NewsBrain()

    def handle_request(self, user_input: str) -> str:
        """
        Método público chamado pelo 'Router' principal do Jarvis.
        Retorna: String com o texto da notícia para ser falado (TTS).
        """
        try:
            logger.info(f"📨 Requisição recebida: {user_input}")
            resposta = self.brain.processar_solicitacao(user_input)
            return resposta
        except Exception as e:
            logger.error(f"❌ Erro crítico no Agente de Notícias: {e}")
            return "Senhor, houve um erro ao processar os feeds de notícias."