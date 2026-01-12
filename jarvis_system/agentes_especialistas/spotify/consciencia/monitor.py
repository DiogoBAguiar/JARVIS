import logging

# Importa os especialistas locais
from .vitals import VitalsMonitor
from .proprioception import ProprioceptionSystem
from .emotional_state import EmotionalStateManager

# Importa dependência externa (sobe 2 níveis para pegar o window.py)
try:
    from ..window import WindowManager
except ImportError:
    # Fallback apenas para garantir que o código não quebre em testes isolados
    import sys
    logging.warning("WindowManager não encontrado. Usando Mock.")
    class WindowManager:
        def obter_hwnd(self): return None

logger = logging.getLogger("CONSCIENCIA_CORE")

class ConscienciaIntegrada:
    """
    Fachada (Facade) que integra Sinais Vitais, Propriocepção e Emoção.
    Substitui a antiga classe monolítica 'ConscienciaCorporal'.
    """
    
    def __init__(self):
        # 1. Sinais Vitais (O Médico): Monitora CPU, RAM, Internet
        self.vitals = VitalsMonitor()
        
        # 2. Emoção (O Psicólogo): Gerencia frustração e memória de erros
        # Passamos o nome do agente para que ele saiba como se identificar no Hipocampo
        self.emotion = EmotionalStateManager(agent_name="spotify_controller")
        
        # 3. Propriocepção (Os Sentidos): Monitora a janela do App
        # Instanciamos o WindowManager aqui para injetar no sistema de propriocepção
        self._window_manager = WindowManager()
        self.proprioception = ProprioceptionSystem(self._window_manager)

    def sentir_sinais_vitais(self):
        """
        Agrega dados de todos os subsistemas em um diagnóstico único.
        Usado pelo agente antes de tentar executar uma ação complexa.
        """
        # Pergunta ao 'Médico'
        saude_sistema = self.vitals.check_system_health()
        tem_internet = self.vitals.check_connectivity()
        
        # Pergunta aos 'Sentidos'
        viu_janela = self.proprioception.verificar_presenca_app()
        tem_foco = self.proprioception.verificar_foco()
        
        # Monta o relatório completo
        diagnostico = {
            "internet": tem_internet,
            "janela_spotify": viu_janela,
            "foco_janela": tem_foco,
            "estado_emocional": self.emotion.estado_atual.value,
            **saude_sistema # Adiciona cpu, memoria, bateria ao dict
        }
        
        return diagnostico

    def refletir_sobre_acao(self, sucesso: bool, contexto: str):
        """
        Recebe o feedback de uma ação (ex: clicou no play?) e processa.
        Se falhar muito, o 'EmotionalStateManager' vai gravar no Hipocampo.
        """
        self.emotion.registrar_experiencia(sucesso, contexto_acao=contexto)
        
        estado = self.emotion.estado_atual
        
        if sucesso:
            logger.debug(f"✨ [Consciência] Sucesso em '{contexto}'. Sentimento: {estado.name}")
        else:
            logger.warning(f"⚠️ [Consciência] Falha em '{contexto}'. Sentimento: {estado.name}")

    def expressar_estado(self):
        """
        Verbaliza como o agente se sente para logs ou respostas ao usuário.
        Ex: 'Estou frustrado, não consigo clicar no botão.'
        """
        return self.emotion.obter_relatorio_emocional()