import os
from groq import Groq
import ollama
from jarvis_system.cortex_frontal.observability import JarvisLogger
# --- IMPORT CORRIGIDO (Agora vem da pasta hipocampo) ---
from jarvis_system.hipocampo.memoria import memoria 

log = JarvisLogger("CORTEX_HYBRID_BRAIN")

# COLOQUE SUA API KEY DA GROQ AQUI
GROQ_API_KEY = "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" 

MODELO_NUVEM = "llama-3.3-70b-versatile"
MODELO_LOCAL = "qwen2:0.5b"

class HybridBrain:
    def __init__(self):
        self.client_groq = None
        if GROQ_API_KEY and "gsk_" in GROQ_API_KEY:
            try:
                self.client_groq = Groq(api_key=GROQ_API_KEY)
            except Exception as e:
                log.error(f"Erro Groq: {e}")

        self.base_system_prompt = (
            "Você é o J.A.R.V.I.S. Responda em Português do Brasil. "
            "Seja breve e prestativo (máximo 2 frases faladas)."
        )

    def pensar(self, texto_usuario: str) -> str:
        # 1. O Cérebro consulta o Hipocampo (RAG)
        contexto_passado = memoria.relembrar(texto_usuario)
        
        prompt_final = texto_usuario
        
        # Se o Hipocampo trouxe lembranças, injetamos no pensamento
        if contexto_passado:
            log.info("Contexto injetado via Hipocampo.")
            prompt_final = (
                f"Memórias relevantes recuperadas do seu banco de dados:\n{contexto_passado}\n\n"
                f"Usuário diz: {texto_usuario}"
            )

        # 2. Processamento Cognitivo (Groq ou Local)
        if self.client_groq:
            return self._pensar_nuvem(prompt_final)
        
        return self._pensar_local(texto_usuario) # Local geralmente não suporta contexto grande

    def _pensar_nuvem(self, prompt: str) -> str:
        try:
            completion = self.client_groq.chat.completions.create(
                model=MODELO_NUVEM,
                messages=[
                    {"role": "system", "content": self.base_system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=150,
            )
            return completion.choices[0].message.content
        except Exception as e:
            log.error(f"Erro Nuvem: {e}")
            return "Erro na conexão neural."

    def _pensar_local(self, texto: str) -> str:
        try:
            response = ollama.chat(model=MODELO_LOCAL, messages=[
                {'role': 'system', 'content': "Seja breve."},
                {'role': 'user', 'content': texto},
            ], options={"num_ctx": 512, "temperature": 0.1})
            return response['message']['content']
        except:
            return "Sistemas cognitivos offline."

    # Método para forçar o aprendizado
    def aprender(self, fato: str):
        return memoria.memorizar(fato)

llm = HybridBrain()