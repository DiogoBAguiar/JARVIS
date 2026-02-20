# jarvis_system/cortex_frontal/brain_llm/main.py
import time
import re
from jarvis_system.cortex_frontal.observability import JarvisLogger

# Mantemos a compatibilidade com o sistema de frases antigas
from jarvis_system.area_broca.frases_padrao import obter_frase

# Módulos Locais
from .keyManager import KeyManager
from .promptFactory import PromptFactory
from .localCloudProviders import CloudProvider, LocalProvider

# Tenta importar memória (Hipocampo)
try:
    from jarvis_system.hipocampo.memoria import memoria
except ImportError:
    memoria = None

class HybridBrain:
    def __init__(self):
        self.log = JarvisLogger("CORTEX_MAIN")
        
        # Inicializa Componentes
        self.key_manager = KeyManager()
        self.cloud = CloudProvider(self.key_manager)
        self.local = LocalProvider()
        
        # Info para logs
        self.categorias_str = "Categorias dinâmicas carregadas via JSON"
        
        self.log.info("🧠 Córtex Frontal (Modular v2.0) Online.")

    def _detectar_intencao_forcada(self, texto: str):
        """Heurística rápida para interceptar comandos óbvios antes do LLM."""
        t = texto.lower().strip()
        verbos_busca = ["tocar", "ouvir", "bota", "reproduzir", "som de", "escutar"]
        
        # Detecção de Música
        for verbo in verbos_busca:
            if re.search(rf"\b{verbo}\s+.{{2,}}", t):
                return f"Comando de música detectado: '{texto}'. Ação esperada: spotify"
        
        # Detecção de Automação (Exemplo)
        if "abrir" in t or "iniciar" in t:
             return f"Comando de sistema detectado: '{texto}'. Ação esperada: sistema/app"
             
        return None

    def pensar(self, texto_usuario: str) -> str:
        start_time = time.time()
        
        # 1. Recuperar Memória (RAG)
        contexto_rag = ""
        if memoria:
            contexto_rag = memoria.relembrar(texto_usuario)
        
        # 2. Dica de Intenção (Pré-processamento)
        dica = self._detectar_intencao_forcada(texto_usuario)
        
        # 3. Montagem do Prompt
        sys_prompt = PromptFactory.build_system_prompt()
        user_prompt = PromptFactory.build_user_prompt(texto_usuario, contexto_rag, dica)
        
        resposta = ""
        provider_used = "NUVEM"

        # 4. Inferência Híbrida (Cloud -> Fallback Local)
        try:
            resposta = self.cloud.generate(sys_prompt, user_prompt)
        except Exception:
            self.log.warning("☁️ Nuvem indisponível. Ativando contingência Local.")
            resposta = self.local.generate(sys_prompt, user_prompt)
            provider_used = "LOCAL"

        # 5. Pós-Processamento (Interceptação de Tags Legadas)
        # Se o LLM responder [[STATUS]], buscamos o texto no cache de frases
        if resposta.startswith("[[") and resposta.endswith("]]"):
            tag = resposta
            frase_cache = obter_frase(tag)
            if frase_cache:
                self.log.info(f"🎯 Cache Hit (Legado): {tag} -> Áudio Otimizado")
                resposta = frase_cache
            else:
                # Se não achar no cache, remove colchetes e fala a tag
                resposta = tag.replace("[[", "").replace("]]", "")

        latency = time.time() - start_time
        self.log.info(f"🤔 Pensamento: {latency:.2f}s ({provider_used})")
        return resposta

    def ensinar(self, fato: str):
        """Interface direta para gravar memórias."""
        if not memoria: return "Erro: Memória off."
        try:
            # Tenta diferentes métodos de compatibilidade com a memória
            if hasattr(memoria, "adicionar_memoria"): memoria.adicionar_memoria(fato)
            elif hasattr(memoria, "memorizar"): memoria.memorizar(fato)
            elif hasattr(memoria, "gravar"): memoria.gravar(fato)
            else: return "Erro técnico na interface de memória."
            
            return "Memória gravada com sucesso."
        except Exception as e:
            self.log.error(f"Erro ao gravar memória: {e}")
            return "Falha ao acessar banco de memória."