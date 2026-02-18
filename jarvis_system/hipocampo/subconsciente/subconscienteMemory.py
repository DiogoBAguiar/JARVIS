import os
import json
import logging

class SubconscienteMemory:
    def __init__(self, memory_path):
        self.memory_path = memory_path
        self.logger = logging.getLogger("SUBCONSCIENTE_MEM")
        
        # Garante que a pasta existe
        os.makedirs(os.path.dirname(self.memory_path), exist_ok=True)

    def carregar(self):
        if os.path.exists(self.memory_path):
            try:
                with open(self.memory_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Erro ao carregar memória: {e}")
        return {"ruido_ignorado": []}

    def salvar(self, dados):
        try:
            with open(self.memory_path, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(f"Erro ao salvar memória: {e}")
            return False

    def atualizar_ruidos(self, novos_ruidos):
        if not novos_ruidos:
            return False
            
        memoria_atual = self.carregar()
        
        # Usa set para evitar duplicatas
        lista_atual = set(memoria_atual.get("ruido_ignorado", []))
        tamanho_antes = len(lista_atual)
        
        lista_atual.update(novos_ruidos)
        
        memoria_atual["ruido_ignorado"] = list(lista_atual)
        
        self.salvar(memoria_atual)
        
        return len(lista_atual) - tamanho_antes # Retorna quantos foram adicionados