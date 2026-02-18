# jarvis_system/cortex_frontal/brain_llm/providers.py
import time
import logging
import ollama
from groq import RateLimitError, APIConnectionError
from .config import MODEL_CLOUD, MODEL_LOCAL, TEMP_CLOUD, TEMP_LOCAL, MAX_TOKENS

log = logging.getLogger("BRAIN_IO")

class CloudProvider:
    def __init__(self, key_manager):
        self.km = key_manager
        self.client = self.km.get_client()

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Tenta gerar resposta usando Groq Cloud com retries e rotação de chaves."""
        if not self.client:
            raise Exception("Sem chaves Groq configuradas.")
        
        tentativas = 3
        for i in range(tentativas):
            try:
                chat = self.client.chat.completions.create(
                    model=MODEL_CLOUD,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=TEMP_CLOUD, 
                    max_tokens=MAX_TOKENS,
                    timeout=8.0 # Timeout agressivo para manter responsividade
                )
                return chat.choices[0].message.content.strip()
            
            except (RateLimitError, APIConnectionError) as e:
                log.warning(f"⚠️ Groq Instável (Tentativa {i+1}/{tentativas}): {e}")
                self.km.rotate()
                self.client = self.km.get_client()
                time.sleep(0.5)
            except Exception as e:
                log.error(f"❌ Erro Groq Genérico: {e}")
                break # Erros genéricos (ex: input inválido) não adiantam tentar de novo
        
        raise Exception("Todas as tentativas de nuvem falharam.")

class LocalProvider:
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Fallback para Ollama Local."""
        try:
            log.info(f"🔻 Usando Modelo Local: {MODEL_LOCAL}")
            response = ollama.chat(
                model=MODEL_LOCAL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "temperature": TEMP_LOCAL, 
                    "num_predict": 256
                }
            )
            return response['message']['content'].strip()
        except Exception as e:
            log.error(f"❌ Erro Ollama Local: {e}")
            return "(serious) Senhor, meus sistemas neurais falharam completamente."