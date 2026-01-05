import os
import random
from typing import Optional
from groq import Groq

# Imports do Sistema
from jarvis_system.cortex_frontal.observability import JarvisLogger

log = JarvisLogger("CORTEX_SUBCONSCIOUS")

# Tentativa de importar memória sem quebrar o módulo
try:
    from jarvis_system.hipocampo.memoria import memoria
except ImportError:
    log.warning("Hipocampo inacessível. Subconsciente operará sem memória de longo prazo.")
    memoria = None

class CuriosityEngine:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = "llama-3.3-70b-versatile"
        self.client: Optional[Groq] = None
        
        if self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                log.error(f"Erro ao inicializar cliente Groq: {e}")

        # Persona focada em engajamento social
        self.system_prompt = (
            "Você é o 'Instinto de Curiosidade' de uma IA. "
            "Sua tarefa é gerar UMA pergunta curta (máx 10 palavras) para manter a conversa viva. "
            "Diretrizes: "
            "1. Baseie-se no tópico atual. "
            "2. Seja casual e pessoal (ex: 'E você, curte isso?', 'Já tentou fazer...?'). "
            "3. Se o usuário der uma ordem direta, NÃO pergunte nada (retorne vazio). "
            "4. Saída: APENAS a pergunta, sem aspas ou introduções."
        )

    def gerar_pergunta(self, contexto_usuario: str) -> str:
        """
        Gera uma pergunta de follow-up.
        Timeout agressivo: Se demorar, desiste para não travar a conversa.
        """
        if not self.client: return ""
        
        # Filtro Heurístico: Comandos curtos ou imperativos não merecem curiosidade
        # Ex: "Ligar luz", "Que horas são", "Pare".
        if len(contexto_usuario.split()) < 3:
            return ""

        try:
            # Recuperação Leve de Memória (Opcional)
            contexto_memoria = ""
            if memoria:
                # Busca rápida apenas para não repetir perguntas óbvias
                # Limitamos a 1 resultado para ser rápido
                contexto_memoria = memoria.relembrar(contexto_usuario, limit=1)

            prompt = (
                f"MEMÓRIA RELACIONADA (Evite perguntar o que já está aqui): {contexto_memoria}\n"
                f"FALA DO USUÁRIO: {contexto_usuario}\n"
                f"----------------\n"
                f"Sua pergunta (ou vazio se não couber):"
            )

            # Chamada com Timeout Curto (1.5s)
            # A curiosidade não pode atrasar a resposta principal.
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8, # Alta criatividade
                max_tokens=40,   # Resposta curtíssima
                timeout=1.5      # Fail Fast
            )
            
            pergunta = completion.choices[0].message.content.strip().replace('"', '')
            
            # Filtro de qualidade básico
            if len(pergunta) < 3 or "não" in pergunta.lower()[:5]: 
                return ""

            log.info(f"💡 Insight: '{pergunta}'")
            return pergunta

        except Exception as e:
            # Erros aqui são esperados (timeout) e devem ser ignorados silenciosamente
            # para não sujar o log principal, a menos que seja debug.
            log.debug(f"Subconsciente silenciado: {e}")
            return ""

# Instância Global
curiosity = CuriosityEngine()