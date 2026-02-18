# jarvis_system/cortex_frontal/brain_llm/prompt_factory.py
import datetime
from .config import SYSTEM_PROMPT_TEMPLATE

class PromptFactory:
    @staticmethod
    def build_system_prompt() -> str:
        """Injeta Data e Hora no System Prompt Mestre."""
        now = datetime.datetime.now()
        return SYSTEM_PROMPT_TEMPLATE.format(
            data=now.strftime("%d/%m/%Y"),
            hora=now.strftime("%H:%M")
        )

    @staticmethod
    def build_user_prompt(query: str, context_rag: str = None, intent_hint: str = None) -> str:
        """Monta o prompt do usuário com contexto RAG e dicas de intenção."""
        prompt_parts = []
        
        # 1. Dica de Intenção (Ex: "Parece comando de música")
        if intent_hint:
            prompt_parts.append(f"INSTRUÇÃO DO SISTEMA: {intent_hint}")
            prompt_parts.append("OBEDEÇA A ESTA CLASSIFICAÇÃO.\n")
        
        # 2. RAG (Memória recuperada)
        if context_rag:
            prompt_parts.append(f"MEMÓRIA/CONTEXTO RECUPERADO:\n{context_rag}\n---\n")
            
        # 3. Query do Usuário
        prompt_parts.append(f"USUÁRIO: {query}")
        
        return "".join(prompt_parts)