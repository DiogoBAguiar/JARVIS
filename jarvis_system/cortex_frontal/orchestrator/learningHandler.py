# jarvis_system/cortex_frontal/orchestrator/learning.py
import re
from jarvis_system.cortex_frontal.observability import JarvisLogger

log = JarvisLogger("ORCH_LEARN")

class LearningHandler:
    def __init__(self, reflexos_module):
        self.reflexos = reflexos_module

    def handle(self, text: str) -> tuple[bool, str]:
        """
        Processa comandos de aprendizado rápido.
        Retorna (sucesso, mensagem_resposta).
        """
        patterns = [
            r"aprenda que (.+) significa (.+)",
            r"aprenda que (.+) quer dizer (.+)",
            r"entenda (.+) como (.+)"
        ]
        
        for p in patterns:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                erro, correcao = match.group(1).strip(), match.group(2).strip()
                
                if self.reflexos:
                    ok = self.reflexos.adicionar_correcao(erro, correcao)
                    if ok:
                        return True, f"Entendido. '{erro}' agora será interpretado como '{correcao}'."
                    else:
                        return True, "Houve um erro ao gravar essa correção."
                else:
                    return True, "Módulo de reflexos indisponível."
                    
        return False, ""