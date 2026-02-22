# jarvis_system/cortex_frontal/orchestrator/cognitionHandler.py
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
        
        # 3. Extração Múltipla de JSON (Automação Implacável)
        json_actions_list = self._extract_json(raw_response)
        
        if json_actions_list:
            # Se tem JSON, extraímos o texto puro para falar (removendo os blocos JSON da fala)
            clean_speech = self._remove_json_blocks(raw_response)
            return clean_speech, json_actions_list

        # 4. Curiosidade (Adiciona perguntas para manter papo se não for ação de sistema)
        if self.curiosity:
            if len(raw_response.split()) < 15 and random.random() < 0.3:
                q = self.curiosity.gerar_pergunta(text)
                if q: raw_response += f" ... {q}"

        return raw_response, None

    def _remove_json_blocks(self, text: str) -> str:
        """Limpa o texto da fala removendo os blocos JSON para o sintetizador de voz não os ler."""
        # Remove markdown de blocos de código
        text = re.sub(r'```json\n(.*?)\n```', '', text, flags=re.DOTALL)
        text = re.sub(r'```(.*?)```', '', text, flags=re.DOTALL)
        # Remove arrays crus
        text = re.sub(r'\[\s*\{.*?\}\s*\]', '', text, flags=re.DOTALL)
        return text.strip()

    def _extract_json(self, text: str):
        """
        Caça múltiplos blocos de JSON gerados pelo LLM e funde-os num único Grafo de Tarefas (DAG).
        Resistente a 'text walls' e explicações descritivas da IA.
        """
        tarefas_mestre = []
        
        # 1. Tenta extrair blocos de código Markdown explícitos (```json ... ```)
        blocos_markdown = re.findall(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
        for bloco in blocos_markdown:
            try:
                parsed = json.loads(bloco)
                if isinstance(parsed, list): tarefas_mestre.extend(parsed)
                elif isinstance(parsed, dict): tarefas_mestre.append(parsed)
            except Exception:
                continue
                
        # Se os blocos markdown deram sucesso, retornamos
        if tarefas_mestre:
            return tarefas_mestre

        # 2. Busca por Arrays (Listas JSON brutas)
        # Encontra todos os blocos que abrem com [ e fecham com ] e contêm objetos {}
        matches_arrays = re.findall(r'\[\s*\{.*?\}\s*\]', text, re.DOTALL)
        for match in matches_arrays:
            try:
                parsed = json.loads(match)
                if isinstance(parsed, list):
                    tarefas_mestre.extend(parsed)
            except Exception:
                continue

        # 3. Busca por Objetos Únicos (Fallback)
        # Se não achou arrays, procura objetos soltos
        if not tarefas_mestre:
            matches_objs = re.findall(r'\{\s*".*?\}\s*', text, re.DOTALL)
            for match in matches_objs:
                try:
                    parsed = json.loads(match)
                    if isinstance(parsed, dict) and ("task_id" in parsed or "ferramenta" in parsed):
                        tarefas_mestre.append(parsed)
                except Exception:
                    continue

        if tarefas_mestre:
            return tarefas_mestre

        return None