import os
import time
from groq import Groq
import ollama

# Imports do Sistema
from jarvis_system.cortex_frontal.observability import JarvisLogger
# Importa o gerenciador de memória vetorial
from jarvis_system.hipocampo.memoria import memoria 

log = JarvisLogger("CORTEX_HYBRID_BRAIN")

# Configurações de Modelo
MODELO_NUVEM = os.getenv("JARVIS_MODEL_CLOUD", "llama-3.3-70b-versatile")
MODELO_LOCAL = os.getenv("JARVIS_MODEL_LOCAL", "qwen2:0.5b") # Leve e rápido para fallback

class HybridBrain:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.client_groq = None
        
        # Inicialização Segura do Cliente Nuvem
        if self.api_key:
            try:
                self.client_groq = Groq(api_key=self.api_key)
                log.info(f"Córtex Superior (Groq) conectado. Modelo: {MODELO_NUVEM}")
            except Exception as e:
                log.error(f"Falha ao iniciar Córtex Superior: {e}")
        else:
            log.warning("GROQ_API_KEY ausente. Modo LOBO SOLITÁRIO (Apenas Local) ativado.")

        # Persona do Jarvis
        self.system_prompt = (
            "Você é o J.A.R.V.I.S., uma IA assistente avançada. "
            "Responda em Português do Brasil. "
            "Seja extremamente conciso, útil e levemente espirituoso. "
            "Não invente fatos se não souber. Use o contexto fornecido como verdade absoluta."
        )

    def pensar(self, texto_usuario: str) -> str:
        """
        Fluxo de Pensamento:
        1. Hipocampo: Busca memórias relevantes (RAG).
        2. Córtex Superior (Nuvem): Tenta processar com modelo SOTA.
        3. Cérebro Reptiliano (Local): Fallback se a nuvem falhar.
        """
        start_time = time.time()
        
        # 1. Recuperação de Memória (RAG)
        contexto = self._recuperar_contexto(texto_usuario)
        prompt_final = self._construir_prompt(texto_usuario, contexto)

        resposta = ""
        origem = ""

        # 2. Tentativa Nuvem (Prioridade)
        if self.client_groq:
            try:
                resposta = self._pensar_nuvem(prompt_final)
                origem = "NUVEM"
            except Exception as e:
                log.warning(f"Córtex Superior falhou ({e}). Caindo para Local...")
                # Fallback automático ocorre abaixo

        # 3. Tentativa Local (Se NUVEM falhou ou não existe)
        if not resposta:
            resposta = self._pensar_local(prompt_final)
            origem = "LOCAL"

        tempo_total = time.time() - start_time
        log.info(f"Pensamento concluído via {origem} em {tempo_total:.2f}s")
        return resposta

    def ensinar(self, fato: str):
        """
        Método chamado pelo Orchestrator para salvar novas informações.
        Corrigido de 'aprender' para 'ensinar' para manter consistência.
        """
        if not fato: return
        log.info(f"Arquivando nova memória: {fato}")
        try:
            return memoria.memorizar(fato)
        except Exception as e:
            log.error(f"Erro ao gravar no Hipocampo: {e}")
            return "Erro de memória."

    def _recuperar_contexto(self, texto: str) -> str:
        try:
            # Busca semanticamente no banco vetorial
            memoria_recuperada = memoria.relembrar(texto)
            if memoria_recuperada:
                log.debug(f"Contexto injetado: {memoria_recuperada[:50]}...")
                return memoria_recuperada
            return ""
        except Exception as e:
            log.error(f"Erro no Hipocampo: {e}")
            return ""

    def _construir_prompt(self, usuario: str, contexto: str) -> str:
        """Monta o prompt estruturado para reduzir alucinações."""
        if not contexto:
            return usuario
        
        # Formato explícito para separar contexto da pergunta
        return (
            f"Contexto recuperado da memória (use se relevante):\n"
            f"{contexto}\n"
            f"---------------------\n"
            f"Usuário: {usuario}"
        )

    def _pensar_nuvem(self, prompt: str) -> str:
        completion = self.client_groq.chat.completions.create(
            model=MODELO_NUVEM,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3, # Baixa temperatura para fidelidade aos fatos/memória
            max_tokens=300,
            timeout=6.0 
        )
        return completion.choices[0].message.content

    def _pensar_local(self, prompt: str) -> str:
        log.info(f"Ativando modelo local {MODELO_LOCAL}...")
        try:
            response = ollama.chat(
                model=MODELO_LOCAL, 
                messages=[
                    {'role': 'system', 'content': "Seja breve. PT-BR."},
                    {'role': 'user', 'content': prompt},
                ], 
                options={
                    "num_ctx": 2048, # Aumentado para caber o contexto RAG
                    "temperature": 0.1
                }
            )
            return response['message']['content']
        except Exception as e:
            log.critical(f"Falha Total: {e}")
            return "Senhor, meus sistemas cognitivos estão offline."

# Instanciação Singleton
llm = HybridBrain()