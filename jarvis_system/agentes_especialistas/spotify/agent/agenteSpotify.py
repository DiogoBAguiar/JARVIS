import logging
from typing import Optional

# Imports de Infraestrutura (3 níveis acima: agent -> spotify -> especialistas -> base)
from ...base_agente import AgenteEspecialista

# Imports dos Módulos Irmãos (Controller, Consciencia, Brain)
# Note que usamos '..' para acessar a pasta 'spotify'
from ..controller import SpotifyController
from ..consciencia import ConscienciaIntegrada
from ..brain import SpotifyBrain

# Configuração Local
from .configSpotify import AGENT_NAME, TRIGGERS

logger = logging.getLogger("SPOTIFY_MANAGER")

class AgenteSpotify(AgenteEspecialista):
    """
    Gerente do Subsistema Spotify.
    Orquestra o Corpo (Controller), a Mente (Consciência) e o Cérebro (Brain).
    """

    def __init__(self):
        super().__init__()
        logger.info("🔧 Inicializando subsistema Spotify...")

        # 1. Inicializa o Corpo (Execução Mecânica)
        self.controller = SpotifyController()

        # 2. Inicializa a Consciência (Sensoriamento e Emoção)
        self.consciencia = ConscienciaIntegrada()

        # 3. Inicializa o Cérebro (Inteligência e Decisão)
        # Injeção de Dependência: O cérebro recebe as ferramentas que pode usar
        # Atualizado para usar a classe modularizada 'SpotifyBrain'
        self.brain = SpotifyBrain(
            controller=self.controller,
            consciencia=self.consciencia
        )

    @property
    def nome(self): 
        return AGENT_NAME
    
    @property
    def gatilhos(self): 
        return TRIGGERS

    def executar(self, comando: str, **kwargs) -> str:
        """
        Ciclo de Vida da Execução:
        Sentir -> Pensar -> Agir -> Refletir
        """
        logger.info(f"🎧 [Manager] Comando recebido: '{comando}'")

        # PASSO 1: Check-up Vital (Sentir)
        diagnostico = self.consciencia.sentir_sinais_vitais()
        
        if not diagnostico.get("internet", True):
            logger.warning("⛔ Sem internet. Abortando.")
            return "Estou sem conexão com a internet, o Spotify não vai responder."

        if not diagnostico.get("janela_spotify", False):
            logger.info("⚠️ Janela do Spotify não detectada. Tentando iniciar...")
            # O Controller vai tentar abrir, mas é bom saber que estava fechado

        # PASSO 2: Delegação Cognitiva (Pensar & Agir)
        try:
            # O Brain decide qual método do controller chamar
            resposta = self.brain.processar(comando)
        except Exception as e:
            logger.error(f"❌ Erro crítico no cérebro do agente: {e}")
            return f"Tive um erro interno ao processar seu pedido: {str(e)}"

        # PASSO 3: Reflexão (Opcional - Log de estado final)
        humor_atual = self.consciencia.expressar_estado()
        logger.debug(f"🧠 Estado mental pós-ação: {humor_atual}")

        return resposta