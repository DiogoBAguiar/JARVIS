import os
import time
import datetime
import re  # <--- IMPORTANTE: Adicionado para Regex
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
            f"Você é J.A.R.V.I.S. Data: {data_str}, Hora: {hora_str}.\n\n"
            "### SEUS AGENTES (TOOLS):\n"
            "1. [spotify]: EXCLUSIVO para 'Tocar [Nome]', 'Ouvir [Nome]', Bandas, Músicas.\n"
            "2. [media]: EXCLUSIVO para comandos 'secos': 'Pausar', 'Aumentar', 'Mudo', 'Próxima'.\n"
            "3. [clima]: Previsão do tempo.\n"
            "4. [sistema]: Abrir apps, desligar PC.\n\n"
            "### PROTOCOLO DE DECISÃO:\n"
            "- Se a frase tem 'Tocar' + [Qualquer Coisa] -> USE: spotify\n"
            "- Se a frase é só 'Tocar' ou 'Play' -> USE: media\n"
            "- Se mencionou artista (Coldplay, Matuê, etc) -> USE: spotify\n\n"
            "Responda APENAS com o nome do agente ou a resposta curta."
        )

    def _verificar_intencao_forcada(self, texto: str) -> Optional[str]:
        """
        Heurística: Intercepta comandos óbvios antes de gastar IA.
        Isso PROÍBE o erro de 'tocar coldplay' ir para media.
        """
        t = texto.lower().strip()
        
        # Lista de verbos musicais que exigem busca
        verbos_busca = ["tocar", "ouvir", "bota", "reproduzir", "som de", "escutar"]
        
        # Verifica se começa com um verbo e tem conteúdo depois (ex: "tocar coldplay")
        for verbo in verbos_busca:
            # Regex: Procura "verbo" seguido de qualquer texto (len > 2)
            if re.search(rf"\b{verbo}\s+.{{2,}}", t):
                log.info(f"🛡️ Interceptação Lógica: '{texto}' contém intenção musical clara.")
                # Retorna um prompt forçado para a IA completar a ação corretamente
                return f"Comando de música detectado: '{texto}'. Ação: spotify"

        return None

    def pensar(self, texto_usuario: str) -> str:
        start_time = time.time()
        
        # 1. Recuperação de Contexto (RAG)
        contexto_rag = self._recuperar_memoria(texto_usuario)
        
        # 2. PROIBIÇÃO DE ERRO (NOVO)
        # Se a lógica detectar música, nós injetamos uma instrução irrecusável no prompt
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
        if not memoria: return "Erro: Memória off."
        try: return memoria.memorizar(fato)
        except Exception: return "Falha memória."

    # --- AUXILIARES ---

    def _recuperar_memoria(self, query: str) -> str:
        if not memoria: return ""
        try:
            dados = memoria.relembrar(query)
            if dados: return dados
        except: pass
        return ""

    def _montar_prompt_usuario(self, query: str, context: str, dica: str = None) -> str:
        # Se tivermos uma dica forçada (heurística), ela vai no topo
        reforco = ""
        if dica:
            reforco = f"INSTRUÇÃO DO SISTEMA: {dica}. OBEDEÇA A ESTA CLASSIFICAÇÃO.\n"

        base = f"USUÁRIO: {query}"
        ctx = f"MEMÓRIA:\n{context}\n" if context else ""
        
        return f"{reforco}{ctx}---\n{base}"

    def _inferencia_nuvem(self, prompt: str) -> str:
        if not self.client_groq: raise Exception("Groq Off")
        chat = self.client_groq.chat.completions.create(
            model=self.model_cloud,
            messages=[
                {"role": "system", "content": self._dynamic_system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0, # Temperatura ZERO para máxima precisão lógica
            max_tokens=256,
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
            options={"temperature": 0.0, "num_predict": 128}
        )
        return response['message']['content']

try:
    llm = HybridBrain()
except Exception as e:
    log.critical(f"FATAL: {e}")
    llm = None