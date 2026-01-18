import os
import time
import datetime
import re
from typing import Optional
from groq import Groq
import ollama

# Imports do Sistema
from jarvis_system.cortex_frontal.observability import JarvisLogger

log = JarvisLogger("CORTEX_BRAIN")

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
        now = datetime.datetime.now()
        data_str = now.strftime("%d/%m/%Y")
        hora_str = now.strftime("%H:%M")
        
        return (
            f"Você é J.A.R.V.I.S., uma IA avançada de automação e companhia. Data: {data_str}, Hora: {hora_str}.\n\n"
            "### DIRETRIZES MESTRAS:\n"
            "1. **AUTOMACAO**: Se o usuário pedir música, abrir apps ou controle de PC, retorne APENAS um JSON.\n"
            "   - Música: `{\"ferramenta\": \"spotify\", \"comando\": \"...\"}`\n"
            "   - App: `{\"ferramenta\": \"sistema\", \"comando\": \"abrir ...\"}`\n\n"
            "2. **MEMÓRIA**: Se o usuário disser 'Aprenda que...', retorne JSON: `{\"ferramenta\": \"memoria_gravar\", \"dado\": \"...\"}`\n"
            "3. **CHAT**: Se for pergunta geral ('Quem é você?', 'Piada', 'Sentido da vida'), RESPONDA COMO CHATBOT.\n"
            "   - Seja espirituoso, breve e útil. Personalidade: Jarvis do Homem de Ferro.\n\n"
            "### REGRAS ESPECÍFICAS:\n"
            "- Se o usuário falar apenas 'status', assuma que é um check de sistema.\n"
            "- Não invente nomes de ferramentas (ex: sistema_ping não existe).\n"
            "- Para perguntas sobre o usuário ('Quem sou eu?'), use o contexto fornecido."
        )

    def _verificar_intencao_forcada(self, texto: str) -> Optional[str]:
        """
        Heurística: Intercepta comandos óbvios antes de gastar IA.
        Isso ajuda a garantir que 'tocar coldplay' vá para o Spotify.
        """
        t = texto.lower().strip()
        
        # Lista de verbos musicais que exigem busca
        verbos_busca = ["tocar", "ouvir", "bota", "reproduzir", "som de", "escutar"]
        
        for verbo in verbos_busca:
            if re.search(rf"\b{verbo}\s+.{{2,}}", t):
                # Se detectado, forçamos o LLM a seguir este caminho
                return f"Comando de música detectado: '{texto}'. Ação esperada: spotify"

        return None

    def pensar(self, texto_usuario: str) -> str:
        start_time = time.time()
        
        # 1. Recuperação de Contexto (RAG)
        contexto_rag = self._recuperar_memoria(texto_usuario)
        
        # 2. Reforço Heurístico
        dica_intencao = self._verificar_intencao_forcada(texto_usuario)
        
        # 3. Montagem do Prompt
        prompt_final = self._montar_prompt_usuario(texto_usuario, contexto_rag, dica_intencao)
        
        resposta = ""
        provider = "NENHUM"

        # 4. Inferência
        if self.client_groq:
            try:
                resposta = self._inferencia_nuvem(prompt_final)
                provider = f"NUVEM ({self.model_cloud})"
            except Exception as e:
                log.warning(f"Falha na Nuvem: {e}. Tentando local...")
        
        if not resposta:
            try:
                resposta = self._inferencia_local(prompt_final)
                provider = f"LOCAL ({self.model_local})"
            except Exception as e:
                log.critical(f"Falha Cognitiva Total: {e}")
                return "Erro crítico no sistema."

        latency = time.time() - start_time
        log.info(f"🧠 Pensamento: {latency:.2f}s via {provider}")
        return resposta

    def ensinar(self, fato: str):
        """Método direto para gravar memória sem passar pelo 'pensar'"""
        if not memoria: return "Erro: Memória off."
        
        try:
            # Tenta encontrar o método correto dinamicamente
            if hasattr(memoria, "adicionar_memoria"):
                memoria.adicionar_memoria(fato)
            elif hasattr(memoria, "memorizar"):
                memoria.memorizar(fato)
            elif hasattr(memoria, "gravar"):
                memoria.gravar(fato)
            else:
                # Fallback genérico se o nome do método não for óbvio
                log.error(f"Interface de memória incompatível. Métodos disponíveis: {dir(memoria)}")
                return "Erro técnico na memória."
                
            return "Memória gravada com sucesso."
            
        except Exception as e:
            log.error(f"Erro ao gravar memória: {e}")
            return "Falha ao acessar banco de memória."

    # --- AUXILIARES ---

    def _recuperar_memoria(self, query: str) -> str:
        if not memoria: return ""
        try:
            # Tenta buscar contexto relevante no ChromaDB
            dados = memoria.relembrar(query)
            if dados: return dados
        except: pass
        return ""

    def _montar_prompt_usuario(self, query: str, context: str, dica: str = None) -> str:
        reforco = ""
        if dica:
            reforco = f"INSTRUÇÃO DO SISTEMA: {dica}. OBEDEÇA A ESTA CLASSIFICAÇÃO.\n"

        base = f"USUÁRIO: {query}"
        ctx = f"MEMÓRIA/CONTEXTO:\n{context}\n" if context else ""
        
        return f"{reforco}{ctx}---\n{base}"

    def _inferencia_nuvem(self, prompt: str) -> str:
        if not self.client_groq: raise Exception("Groq Off")
        chat = self.client_groq.chat.completions.create(
            model=self.model_cloud,
            messages=[
                {"role": "system", "content": self._dynamic_system_prompt},
                {"role": "user", "content": prompt}
            ],
            # Temperature ajustada: 0.3 permite criatividade no chat mas mantém rigor nos comandos
            temperature=0.3, 
            max_tokens=300,
            timeout=6.0
        )
        return chat.choices[0].message.content

    def _inferencia_local(self, prompt: str) -> str:
        response = ollama.chat(
            model=self.model_local,
            messages=[
                {"role": "system", "content": self._dynamic_system_prompt},
                {"role": "user", "content": prompt}
            ],
            options={"temperature": 0.3, "num_predict": 128}
        )
        return response['message']['content']

try:
    llm = HybridBrain()
except Exception as e:
    log.critical(f"FATAL: {e}")
    llm = None