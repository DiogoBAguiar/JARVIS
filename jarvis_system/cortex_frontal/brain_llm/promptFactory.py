# jarvis_system/cortex_frontal/brain_llm/promptFactory.py
import datetime
from .config import SYSTEM_PROMPT_TEMPLATE

class PromptFactory:
    @staticmethod
    def build_system_prompt(tool_catalog: str = "") -> str:
        """Injeta Data, Hora, Catálogo Dinâmico e a Diretiva Zero no System Prompt Mestre."""
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
            
            # =========================================================
            # DIRETIVA ZERO ABSOLUTA (BLINDAGEM ANTI-ALUCINAÇÃO)
            # =========================================================
            base_prompt += "\n\n### 6. DIRETIVA ZERO (REGRAS ESTRITAS DE EXECUÇÃO):\n"
            base_prompt += "Aja EXATAMENTE de acordo com as 3 regras abaixo, sem exceções:\n"
            base_prompt += "1. PROIBIDO INVENTAR: Você SÓ pode usar as ferramentas listadas no catálogo acima. NUNCA invente ferramentas como 'calculadora', 'explicador', 'pesquisa' ou nomes de jogos.\n"
            base_prompt += "2. APPS = FERRAMENTA SISTEMA: Se a intenção for abrir, iniciar, rodar ou fechar QUALQUER aplicativo local, jogo ou site (ex: League of Legends, Calculadora, Bloco de Notas), você DEVE usar a ferramenta 'sistema' passando o nome no parâmetro 'comando'.\n"
            base_prompt += "3. CONVERSA = TEXTO PURO: Se o usuário fizer uma pergunta de conhecimento geral (ex: sentido da vida, explicar um conceito), pedir para fazer uma conta de matemática, ou quiser conversar, NÃO USE FERRAMENTAS. NÃO GERE JSON para essas intenções. Responda diretamente com o texto da resposta, de forma natural.\n"
            # =========================================================
            # FEW-SHOT: EXEMPLO OBRIGATÓRIO (MATA AS FERRAMENTAS FANTASMAS)
            # =========================================================
            base_prompt += "\n\n### 7. EXEMPLO DE GRAFO DE TAREFAS OBRIGATÓRIO:\n"
            base_prompt += "Se o usuário disser: 'abra a calculadora, explique o que é um átomo e toque coldplay', você DEVE gerar:\n"
            base_prompt += "[\n"
            base_prompt += "  {\"task_id\": \"t1\", \"target_tool\": \"sistema\", \"initial_args\": {\"comando\": \"abrir calculadora\"}, \"dependencies\": []},\n"
            base_prompt += "  {\"task_id\": \"t2\", \"target_tool\": \"spotify\", \"initial_args\": {\"comando\": \"tocar coldplay\"}, \"dependencies\": []}\n"
            base_prompt += "]\n"
            base_prompt += "(NOTA: A explicação sobre o átomo foi processada mentalmente e não gerou tarefa no JSON. Ferramentas inexistentes NUNCA são inventadas.)\n"
            
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