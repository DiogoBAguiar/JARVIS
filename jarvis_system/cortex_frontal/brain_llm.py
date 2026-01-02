import ollama
from jarvis_system.cortex_frontal.observability import JarvisLogger

log = JarvisLogger("CORTEX_LLM")

# Defina o modelo que você baixou no terminal (ex: llama3.2, llama3, mistral)
MODELO_ATIVO = "llama3.2"

class LLMService:
    """
    Interface de comunicação com a Inteligência Artificial Local (Ollama).
    """
    def __init__(self):
        self.contexto_sistema = (
            "Você é o J.A.R.V.I.S, uma inteligência artificial assistente. "
            "Responda sempre em Português do Brasil. "
            "Suas respostas serão faladas em voz alta, então SEJA BREVE. "
            "Máximo de 2 frases. Não use listas, markdown ou blocos de código. "
            "Seja direto, útil e levemente formal."
        )

    def pensar(self, texto_usuario: str) -> str:
        """
        Envia o texto para o modelo e retorna a resposta.
        """
        log.info(f"Enviando para o Llama ({MODELO_ATIVO})...")
        
        try:
            response = ollama.chat(model=MODELO_ATIVO, messages=[
                {'role': 'system', 'content': self.contexto_sistema},
                {'role': 'user', 'content': texto_usuario},
            ])
            
            resposta_ia = response['message']['content']
            log.info(f"Pensamento gerado: '{resposta_ia}'")
            return resposta_ia

        except Exception as e:
            # Captura erros comuns (Ollama desligado, modelo não baixado)
            log.error(f"Falha na sinapse neural: {e}")
            if "connection refused" in str(e).lower():
                return "Meus sistemas cognitivos estão offline. Verifique se o Ollama está rodando."
            return "Não consegui processar esse pensamento."

# Instância Singleton
llm = LLMService()