import logging
from enum import Enum

# IMPORTAÇÃO DA CONEXÃO NEURAL (Global)
# Ajuste o caminho relativo conforme a estrutura exata das suas pastas
from jarvis_system.hipocampo.memoria import memoria 

logger = logging.getLogger("CONSCIENCIA_EMOCIONAL")

class Emotion(Enum):
    CONFIANTE = "😌 Confiante"
    NEUTRO = "😐 Neutro"
    CONFUSO = "🤔 Confuso"
    FRUSTRADO = "😣 Frustrado"
    EMPOLGADO = "🤩 Empolgado"

class EmotionalStateManager:
    """
    Gerencia o estado psicológico local e reporta eventos significativos
    ao Hipocampo (Memória de Longo Prazo).
    """
    
    def __init__(self, agent_name="spotify"):
        self.agent_name = agent_name
        self.estado_atual = Emotion.NEUTRO
        self.consecutive_errors = 0
        self.consecutive_success = 0

    def registrar_experiencia(self, sucesso: bool, contexto_acao: str):
        """
        Processa o resultado imediato e decide se deve incomodar o cérebro principal.
        """
        estado_anterior = self.estado_atual

        if sucesso:
            self.consecutive_errors = 0
            self.consecutive_success += 1
            self._atualizar_humor_sucesso()
        else:
            self.consecutive_success = 0
            self.consecutive_errors += 1
            self._atualizar_humor_fracasso()

        # --- SINAPSE COM O HIPOCAMPO ---
        # Só gravamos na memória permanente se houver uma mudança de estado relevante
        # ou se for uma falha crítica (Frustração). Não queremos gravar tudo.
        
        if self.estado_atual == Emotion.FRUSTRADO and estado_anterior != Emotion.FRUSTRADO:
            logger.info("⚡ Enviando sinal de dor/frustração ao Hipocampo...")
            memoria.memorizar_episodio(
                agente=self.agent_name,
                acao=contexto_acao,
                resultado="FALHA_CRITICA",
                emocao=self.estado_atual.name,
                detalhes=f"Falhou {self.consecutive_errors} vezes consecutivas."
            )
            
        elif self.estado_atual == Emotion.EMPOLGADO and estado_anterior != Emotion.EMPOLGADO:
            logger.info("⚡ Enviando sinal de dopamina/sucesso ao Hipocampo...")
            memoria.memorizar_episodio(
                agente=self.agent_name,
                acao=contexto_acao,
                resultado="SUCESSO_PLENO",
                emocao=self.estado_atual.name,
                detalhes="Fluxo de execução perfeito detectado."
            )

    def _atualizar_humor_sucesso(self):
        if self.consecutive_success > 5:
            self.estado_atual = Emotion.EMPOLGADO
        else:
            self.estado_atual = Emotion.CONFIANTE

    def _atualizar_humor_fracasso(self):
        if self.consecutive_errors >= 3:
            self.estado_atual = Emotion.FRUSTRADO
        elif self.consecutive_errors > 0:
            self.estado_atual = Emotion.CONFUSO

    def obter_relatorio_emocional(self) -> str:
        # (O mesmo código de retorno de string anterior...)
        return f"Estado: {self.estado_atual.value}"