import os
import logging
import json
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

# --- AGENTE DE SEGURANÇA (SAFE AGENT) ---
class SafeAgent:
    def __init__(self, agent_real):
        self.agent = agent_real
        self.mock = MockAgent()
        
        self.backup_cloud_models = [] 
        self.backup_local = None
        
        if not AGNO_AVAILABLE: return

        # 1. Configura Backups Gemini com a SUA Lista Específica
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            # Lista exata baseada no seu painel
            model_names = [
                "gemini-2.5-flash",       # Prioridade Máxima
                "gemini-2.5-flash-lite",  # Backup Rápido
                "gemini-3-flash",         # Modelo Novo
                "gemma-3-27b",            # Gemma Grande
                "gemma-3-12b",            # Gemma Médio
                "gemini-1.5-flash"        # Fallback Clássico (Segurança)
            ]
            
            for m_name in model_names:
                try:
                    # Instancia o modelo com o ID específico
                    self.backup_cloud_models.append(Gemini(id=m_name, api_key=gemini_key))
                except: pass

        # 2. Configura Backup Local (Ollama)
        local_model_id = os.getenv("JARVIS_MODEL_LOCAL")
        if local_model_id:
            try:
                self.backup_local = Ollama(id=local_model_id)
            except: pass

    def _validar_e_filtrar(self, response):
        """Retorna False se a resposta for um erro."""
        if response is None: return False
        if not hasattr(response, 'content'): return False
        
        conteudo = str(response.content).strip()
        if not conteudo: return False
        
        # Lista Negra de Erros (Groq, Gemini, Ollama)
        erros_comuns = [
            '{"error":', '"code":', 'Rate limit reached', '429 Too Many Requests',
            '404 NOT_FOUND', 'not found for API version', 'RESOURCE_EXHAUSTED',
            'quota exceeded', 'llama runner process has terminated', 
            'exit status 2', 'Internal Server Error'
        ]
        
        for erro in erros_comuns:
            if erro.lower() in conteudo.lower():
                return False 
        return True

    def run(self, prompt):
        # 1. TENTA GROQ (Principal)
        try:
            response = self.agent.run(prompt)
            if self._validar_e_filtrar(response): return response
        except Exception: pass

        # 2. TENTA GEMINI (Itera sobre a lista gemini-2.5, gemma-3, etc.)
        if self.backup_cloud_models:
            for gemini_model in self.backup_cloud_models:
                try:
                    # logger.info(f"🔄 Tentando modelo: {gemini_model.id}...")
                    self.agent.model = gemini_model
                    response = self.agent.run(prompt)
                    if self._validar_e_filtrar(response): 
                        # logger.info(f"✅ Sucesso com {gemini_model.id}")
                        return response
                except Exception: 
                    continue # Tenta o próximo da lista

        # 3. TENTA LOCAL (Ollama)
        if self.backup_local:
            try:
                self.agent.model = self.backup_local
                response = self.agent.run(prompt)
                if self._validar_e_filtrar(response): return response
            except Exception: pass

        # 4. MOCK (Último recurso)
        logger.error("🛑 Todos os modelos falharam. Ativando Mock JSON.")
        return self.mock.run(prompt)

# --- FÁBRICA ---
class LLMFactory:
    @staticmethod
    def get_model(preferred_model: str = "llama-3.3-70b-versatile"):
        if not AGNO_AVAILABLE: return None
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key: return Groq(id=preferred_model, api_key=groq_key)
        
        # Se não tiver Groq, tenta o primeiro da lista nova como padrão
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key: return Gemini(id="gemini-2.5-flash", api_key=gemini_key)
        
        return None