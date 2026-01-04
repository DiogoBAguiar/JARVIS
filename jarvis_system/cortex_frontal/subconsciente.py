import os
import random
from groq import Groq
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.hipocampo.memoria import memoria

log = JarvisLogger("CORTEX_SUBCONSCIENTE")

class CuriosityEngine:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.client = None
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
        
        # Este prompt define a "Outra IA" que você pediu.
        # Ela não é servil, ela é analítica e curiosa.
        self.system_prompt = (
            "Você é o Módulo de Curiosidade do JARVIS. "
            "Sua função NÃO é responder o usuário, mas sim descobrir o que falta aprender sobre ele. "
            "Analise o contexto e gere UMA ÚNICA pergunta curta e casual para extrair informações úteis "
            "(hobbies, rotinas, preferências, trabalho, sonhos). "
            "Seja natural, como um amigo querendo conhecer o outro. Fale em PT-BR."
        )

    def gerar_pergunta(self, contexto_atual: str) -> str:
        """
        Analisa o papo atual e decide uma pergunta para aprofundar o conhecimento.
        """
        if not self.client: return ""

        # Recupera memórias antigas para não perguntar o que já sabe
        memoria_existente = memoria.relembrar("quem sou eu fatos sobre mim preferencias")
        
        prompt = (
            f"O QUE JÁ SEI SOBRE O USUÁRIO:\n{memoria_existente}\n\n"
            f"CONVERSA ATUAL: {contexto_atual}\n\n"
            f"MISSÃO: Com base no que eu já sei (ou não sei), faça uma pergunta para aprender algo novo sobre o usuário. "
            f"A pergunta deve fazer sentido com a conversa atual ou ser uma curiosidade aleatória se o papo estiver morno."
        )

        try:
            log.info("Analisando lacunas de conhecimento...")
            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile", # Usamos o modelo potente para ter "sacadas" inteligentes
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7, # Criatividade mais alta para variar as perguntas
                max_tokens=60
            )
            pergunta = completion.choices[0].message.content.replace('"', '')
            return pergunta
        except Exception as e:
            log.error(f"Falha na curiosidade: {e}")
            return ""

# Singleton
curiosity = CuriosityEngine()