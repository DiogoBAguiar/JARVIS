from ..base_agente import AgenteEspecialista
from .nlu import SpotifyAgnoAgent

class AgenteSpotify(AgenteEspecialista):
    def __init__(self):
        # Inicializamos o cérebro Agno aqui
        self.agno_brain = SpotifyAgnoAgent()

    @property
    def nome(self): return "spotify"
    
    @property
    def gatilhos(self): 
        return [
            "spotify", "tocar", "play", "musica", "pausa", 
            "relatório", "clique", "pular", "voltar", "ouvir"
        ]

    def executar(self, comando: str, **kwargs) -> str:
        # Repassa o comando para o Agno resolver
        print(f"🤖 [Agno] Processando: {comando}")
        resposta = self.agno_brain.processar(comando)
        return resposta