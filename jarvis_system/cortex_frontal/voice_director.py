import os
from groq import Groq

class VoiceDirector:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=self.api_key) if self.api_key else None
        
        # As tags oficiais que seu Fish Audio aceita (baseado na documentação que você mandou)
        self.emocoes_validas = [
            "confident", "sincere", "worried", "anxious", 
            "serious", "sarcastic", "amused", "whispering", 
            "indifferent", "satisfied", "angry", "shouting"
        ]

    def analisar_tom(self, frase: str) -> str:
        """
        A I.A. lê a frase e escolhe a melhor tag de emoção.
        """
        if not self.client:
            return "confident" # Fallback padrão se estiver offline

        prompt = f"""
        Aja como um Diretor de Voz para o assistente JARVIS.
        Analise a frase abaixo e escolha a ÚNICA melhor emoção da lista para ser usada na síntese de voz (TTS).

        LISTA DE EMOÇÕES PERMITIDAS:
        {", ".join(self.emocoes_validas)}

        REGRAS:
        1. Se for uma confirmação ou dado técnico, use 'confident' ou 'indifferent'.
        2. Se for um perigo ou erro grave, use 'worried' ou 'serious'.
        3. Se for uma piada ou ironia, use 'sarcastic' ou 'amused'.
        4. Se for algo furtivo, use 'whispering'.
        5. Retorne APENAS a palavra da emoção. Nada mais.

        FRASE: "{frase}"
        EMOÇÃO ESCOLHIDA:
        """

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile", # Modelo rápido e inteligente
                temperature=0.1, # Baixa temperatura para ser consistente
                max_tokens=10
            )
            
            emocao_detectada = chat_completion.choices[0].message.content.strip().lower()
            
            # Limpeza extra caso a IA retorne pontuação
            for emo in self.emocoes_validas:
                if emo in emocao_detectada:
                    return emo
            
            return "confident" # Padrão se a IA alucinar

        except Exception as e:
            print(f"Erro no Diretor de Voz: {e}")
            return "confident"