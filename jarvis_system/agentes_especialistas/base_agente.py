from abc import ABC, abstractmethod

class AgenteEspecialista(ABC):
    """
    Classe base para todos os especialistas (Calendar, Spotify, Email, etc).
    """
    
    @property
    @abstractmethod
    def nome(self) -> str:
        """Nome único do agente (ex: 'calendario', 'spotify')."""
        pass

    @property
    @abstractmethod
    def gatilhos(self) -> list:
        """Palavras-chave que ajudam o sistema a identificar este agente (opcional com LLM)."""
        pass

    @abstractmethod
    def executar(self, comando: str, **kwargs) -> str:
        """
        Lógica principal.
        Recebe o comando (ex: 'agendar reunião amanhã') e retorna a resposta de texto.
        """
        pass