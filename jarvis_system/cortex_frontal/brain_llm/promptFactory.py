# jarvis_system/cortex_frontal/brain_llm/promptFactory.py
import datetime
from .config import SYSTEM_PROMPT_TEMPLATE

class PromptFactory:
    @staticmethod
    def build_system_prompt(tool_catalog: str = "") -> str:
        """Injeta Data, Hora e o Catálogo Dinâmico de Ferramentas (Fase 3) no System Prompt Mestre."""
        now = datetime.datetime.now()
        
        # 1. Formata a base com data e hora (já com a correção das chaves {{}})
        base_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            data=now.strftime("%d/%m/%Y"),
            hora=now.strftime("%H:%M")
        )
        
        # 2. FASE 3: Injeção Dinâmica do Catálogo
        if tool_catalog:
            base_prompt += "\n\n### 5. CATÁLOGO DE FERRAMENTAS DISPONÍVEIS:\n"
            base_prompt += "Você pode usar as seguintes ferramentas no seu Grafo de Tarefas (DAG):\n"
            base_prompt += tool_catalog
            
        return base_prompt

    @staticmethod
    def build_user_prompt(query: str, context_rag: str = None, intent_hint: str = None) -> str:
        """Monta o prompt do usuário com contexto RAG e dicas de intenção."""
        prompt_parts = []
        
        # 1. Dica de Intenção (Ex: "Parece comando de música")
        if intent_hint:
            prompt_parts.append(f"INSTRUÇÃO DO SISTEMA: {intent_hint}\n")
            prompt_parts.append("OBEDEÇA A ESTA CLASSIFICAÇÃO.\n")
        
        # 2. RAG (Memória recuperada)
        if context_rag:
            prompt_parts.append(f"MEMÓRIA/CONTEXTO RECUPERADO:\n{context_rag}\n---\n")
            
        # 3. Query do Usuário
        prompt_parts.append(f"USUÁRIO: {query}")
        
        return "".join(prompt_parts)