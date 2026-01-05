import os
import time
import datetime
from typing import Optional
from groq import Groq
import ollama

# Imports do Sistema
from jarvis_system.cortex_frontal.observability import JarvisLogger

log = JarvisLogger("CORTEX_BRAIN")

# Tenta importar memória de forma segura
try:
    from jarvis_system.hipocampo.memoria import memoria
except ImportError:
    log.warning("Hipocampo (Memória) não encontrado ou falhou ao carregar.")
    memoria = None

class HybridBrain:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model_cloud = os.getenv("JARVIS_MODEL_CLOUD", "llama-3.3-70b-versatile")
        self.model_local = os.getenv("JARVIS_MODEL_LOCAL", "qwen2:0.5b")
        
        self.client_groq: Optional[Groq] = None
        self._initialize_cloud()

    def _initialize_cloud(self):
        """Conexão lazy/resiliente com a nuvem."""
        if self.api_key:
            try:
                self.client_groq = Groq(api_key=self.api_key)
                log.info(f"☁️ Córtex Nuvem Conectado: {self.model_cloud}")
            except Exception as e:
                log.error(f"❌ Erro ao conectar Groq: {e}")
        else:
            log.warning("⚠️ Modo Offline Forçado (Sem API Key).")

    @property
    def _dynamic_system_prompt(self) -> str:
        """Gera o prompt do sistema com contexto temporal atualizado."""
        now = datetime.datetime.now()
        data_str = now.strftime("%d/%m/%Y")
        hora_str = now.strftime("%H:%M")
        
        return (
            f"Você é J.A.R.V.I.S., uma IA assistente técnica e eficiente. "
            f"Hoje é {data_str}, são {hora_str}. "
            "Diretrizes: "
            "1. Responda em Português do Brasil. "
            "2. Seja direto, profissional e levemente sarcástico quando apropriado. "
            "3. Não invente dados. Se não souber, diga que precisa pesquisar. "
            "4. Respostas curtas são preferíveis para síntese de voz."
        )

    def pensar(self, texto_usuario: str) -> str:
        """Processo Cognitivo: RAG -> Cloud -> Local Fallback"""
        start_time = time.time()
        
        # 1. Recuperação de Contexto (RAG)
        contexto_rag = self._recuperar_memoria(texto_usuario)
        
        # 2. Construção do Prompt
        prompt_final = self._montar_prompt_usuario(texto_usuario, contexto_rag)
        
        resposta = ""
        provider = "NENHUM"

        # 3. Tentativa Nuvem
        if self.client_groq:
            try:
                resposta = self._inferencia_nuvem(prompt_final)
                provider = f"NUVEM ({self.model_cloud})"
            except Exception as e:
                log.warning(f"Falha na Nuvem: {e}. Tentando local...")
        
        # 4. Fallback Local
        if not resposta:
            try:
                resposta = self._inferencia_local(prompt_final)
                provider = f"LOCAL ({self.model_local})"
            except Exception as e:
                log.critical(f"Falha Cognitiva Total: {e}")
                return "Meus sistemas lógicos falharam, senhor."

        latency = time.time() - start_time
        log.info(f"🧠 Pensamento: {latency:.2f}s via {provider}")
        return resposta

    def ensinar(self, fato: str):
        """Interface para gravar memórias."""
        if not memoria:
            log.error("Hipocampo indisponível para gravação.")
            return "Erro: Memória desativada."
        
        try:
            # Assumimos que o módulo memoria tem tratamento de erro interno
            return memoria.memorizar(fato)
        except Exception as e:
            log.error(f"Erro ao ensinar fato: {e}")
            return "Falha na consolidação de memória."

    # --- MÉTODOS PRIVADOS (Auxiliares) ---

    def _recuperar_memoria(self, query: str) -> str:
        if not memoria: return ""
        try:
            # Timeout conceitual (se a lib suportasse, usaríamos aqui)
            dados = memoria.relembrar(query)
            if dados:
                return dados
        except Exception as e:
            log.warning(f"RAG falhou, seguindo sem memória: {e}")
        return ""

    def _montar_prompt_usuario(self, query: str, context: str) -> str:
        if not context:
            return query
        
        return (
            f"DADOS RECUPERADOS DA MEMÓRIA:\n{context}\n"
            f"-----------------------------------\n"
            f"USUÁRIO: {query}"
        )

    def _inferencia_nuvem(self, prompt: str) -> str:
        if not self.client_groq: raise Exception("Cliente Groq não inicializado")
        
        chat = self.client_groq.chat.completions.create(
            model=self.model_cloud,
            messages=[
                {"role": "system", "content": self._dynamic_system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3, # Focado e preciso
            max_tokens=256,  # Respostas curtas para voz
            timeout=5.0      # Fail fast: se demorar 5s, aborte e vá para local
        )
        return chat.choices[0].message.content

    def _inferencia_local(self, prompt: str) -> str:
        # Ollama roda localmente, pode demorar, mas é garantido (se a RAM aguentar)
        response = ollama.chat(
            model=self.model_local,
            messages=[
                {"role": "system", "content": "Seja conciso. PT-BR."},
                {"role": "user", "content": prompt}
            ],
            options={"temperature": 0.1, "num_predict": 128}
        )
        return response['message']['content']

# --- INSTÂNCIA GLOBAL (SINGLETON) ---
# Mantida para compatibilidade com orchestrator.py
# Em um refactor futuro, o Kernel deveria injetar isso.
try:
    llm = HybridBrain()
except Exception as e:
    log.critical(f"FATAL: Não foi possível criar o Cérebro: {e}")
    llm = None