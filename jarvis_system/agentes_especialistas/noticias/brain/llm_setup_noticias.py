import os
import logging
import json
import random
from typing import Optional

# Tenta importar os modelos do Agno
try:
    from agno.models.google import Gemini
    from agno.models.groq import Groq
    from agno.models.ollama import Ollama
    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False

logger = logging.getLogger("NEWS_BRAIN_LLM")

# --- MÓDULO DE SIMULAÇÃO (MOCK) ---
class MockResponse:
    def __init__(self, content):
        self.content = content

class MockAgent:
    def __init__(self, model_id="mock"):
        self.model_id = model_id
        self.mocks = self._carregar_mocks()

    def _carregar_mocks(self):
        try:
            base_path = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(base_path, "mocks.json")
            if not os.path.exists(json_path): return None
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return None

    def run(self, prompt):
        logger.warning("⚠️ MOCK ATIVO: Usando resposta simulada (JSON).")
        prompt_lower = prompt.lower()
        scenario_match = None

        if self.mocks and "scenarios" in self.mocks:
            for scenario in self.mocks["scenarios"]:
                if any(k in prompt_lower for k in scenario["keywords"]):
                    scenario_match = scenario
                    break
        
        if not scenario_match and self.mocks:
            scenario_match = self.mocks.get("default")

        if "json" in prompt_lower or "schema" in prompt_lower:
            response_data = scenario_match["router"] if scenario_match else {"intent": "briefing", "complexity": "low"}
            return MockResponse(json.dumps(response_data))
        else:
            text_content = scenario_match["synthesis"] if scenario_match else "Modo de simulação ativo."
            return MockResponse(text_content)

# --- GERENCIADOR DE CHAVES ---
def get_all_groq_keys():
    """Varre o ambiente em busca de todas as chaves GROQ_API_KEY_*"""
    keys = []
    # Procura chaves com sufixo (Ex: GROQ_API_KEY_1, GROQ_API_KEY_ABC)
    for var_name, value in os.environ.items():
        if var_name.startswith("GROQ_API_KEY") and value.strip():
            keys.append(value)
    
    # Remove duplicatas e embaralha para balancear carga
    unique_keys = list(set(keys))
    # random.shuffle(unique_keys) # Descomente se quiser ordem aleatória
    return unique_keys

# --- AGENTE DE SEGURANÇA (SAFE AGENT) ---
class SafeAgent:
    def __init__(self, agent_real):
        self.agent = agent_real
        self.mock = MockAgent()
        
        self.groq_pool = [] # Piscina de modelos Groq (várias chaves)
        self.backup_cloud_models = []
        self.backup_local = None
        
        if not AGNO_AVAILABLE: return

        # 1. Configura Pool de Chaves Groq (ROTAÇÃO)
        groq_keys = get_all_groq_keys()
        if groq_keys:
            logger.info(f"🔑 Groq: {len(groq_keys)} chaves de API detectadas e carregadas.")
            for key in groq_keys:
                try:
                    # Cria uma instância do modelo para cada chave
                    model_instance = Groq(id="llama-3.3-70b-versatile", api_key=key)
                    self.groq_pool.append(model_instance)
                except: pass
        else:
            logger.warning("⚠️ Nenhuma chave GROQ encontrada no .env")

        # 2. Configura Backups Gemini
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            model_names = [
                "gemini-2.5-flash", "gemini-2.5-flash-lite", 
                "gemini-1.5-flash", "gemini-pro"
            ]
            for m_name in model_names:
                try:
                    self.backup_cloud_models.append(Gemini(id=m_name, api_key=gemini_key))
                except: pass

        # 3. Configura Backup Local
        local_model_id = os.getenv("JARVIS_MODEL_LOCAL")
        if local_model_id:
            try:
                self.backup_local = Ollama(id=local_model_id)
            except: pass

    def _validar_e_filtrar(self, response):
        if response is None: return False
        if not hasattr(response, 'content'): return False
        
        conteudo = str(response.content).strip()
        if not conteudo: return False
        
        # Lista Negra de Erros
        erros_comuns = [
            '{"error":', '"code":', 'Rate limit reached', '429 Too Many Requests',
            '404 NOT_FOUND', 'not found for API version', 'RESOURCE_EXHAUSTED',
            'quota exceeded', 'llama runner process has terminated', 
            'exit status 2', 'Internal Server Error'
        ]
        
        for erro in erros_comuns:
            if erro.lower() in conteudo.lower(): return False 
        return True

    def run(self, prompt):
        # 1. TENTA ROTAÇÃO DE CHAVES GROQ
        # Se tivermos chaves, tentamos uma por uma até funcionar
        if self.groq_pool:
            for i, groq_model in enumerate(self.groq_pool):
                try:
                    # logger.info(f"🔄 Tentando Groq Key #{i+1}...")
                    self.agent.model = groq_model
                    response = self.agent.run(prompt)
                    if self._validar_e_filtrar(response): 
                        return response # SUCESSO! Sai da função.
                    else:
                        # Se falhou (429), o loop continua para a próxima chave
                        logger.warning(f"⚠️ Groq Key #{i+1} falhou (Limite/Erro). Trocando chave...")
                except Exception: 
                    continue 

        # 2. TENTA ROTAÇÃO DE MODELOS GEMINI
        if self.backup_cloud_models:
            for gemini_model in self.backup_cloud_models:
                try:
                    self.agent.model = gemini_model
                    response = self.agent.run(prompt)
                    if self._validar_e_filtrar(response): return response
                except Exception: continue

        # 3. TENTA LOCAL (OLLAMA)
        if self.backup_local:
            try:
                self.agent.model = self.backup_local
                response = self.agent.run(prompt)
                if self._validar_e_filtrar(response): return response
            except Exception: pass

        # 4. MOCK (ÚLTIMO RECURSO)
        logger.error("🛑 Todas as chaves/modelos falharam. Ativando Mock.")
        return self.mock.run(prompt)

# --- FÁBRICA ---
class LLMFactory:
    @staticmethod
    def get_model(preferred_model: str = "llama-3.3-70b-versatile"):
        if not AGNO_AVAILABLE: return None
        
        # Pega a primeira chave que encontrar só para inicializar o Agente
        # (O SafeAgent vai substituir isso depois com o pool de chaves)
        keys = get_all_groq_keys()
        if keys:
            return Groq(id=preferred_model, api_key=keys[0])
        
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key: return Gemini(id="gemini-1.5-flash", api_key=gemini_key)
        
        return None