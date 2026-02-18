# jarvis_system/cortex_frontal/orchestrator/cognition.py
import json
import re
import random
from .configOrchestrator import MEMORY_TRIGGERS
from jarvis_system.cortex_frontal.observability import JarvisLogger

log = JarvisLogger("ORCH_COG")

class CognitionHandler:
    def __init__(self, brain_llm, curiosity_module):
        self.brain = brain_llm
        self.curiosity = curiosity_module

    def process(self, text: str) -> tuple[str, dict]:
        """
        Processa o texto usando o LLM.
        Retorna (resposta_fala, acao_json_opcional).
        """
        if not self.brain:
            return "Estou desconectado do meu cérebro.", None

        # 1. Memória Explícita (Regex antes do LLM para garantir)
        for trigger in MEMORY_TRIGGERS:
            if trigger in text and "aprenda que" not in text:
                payload = text.split(trigger, 1)[1].strip()
                if payload:
                    self.brain.ensinar(payload)
                    return f"Memorizado: {payload}", None

        # 2. Pensamento (LLM)
        raw_response = self.brain.pensar(text)
        
        # 3. Extração de JSON (Automação)
        json_action = self._extract_json(raw_response)
        if json_action:
            # Se tem JSON, a prioridade é a ação, não a fala do LLM
            return "", json_action

        # 4. Curiosidade (Adiciona perguntas para manter papo)
        if self.curiosity:
            if len(raw_response.split()) < 15 and random.random() < 0.3:
                q = self.curiosity.gerar_pergunta(text)
                if q: raw_response += f" ... {q}"

        return raw_response, None

    def _extract_json(self, text: str) -> dict:
        try:
            if "{" in text and "}" in text:
                match = re.search(r'\{.*\}', text, re.DOTALL)
                if match:
                    return json.loads(match.group(0))
        except Exception as e:
            log.warning(f"Falha ao parsear JSON do LLM: {e}")
        return None