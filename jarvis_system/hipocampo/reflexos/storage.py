import os
import json
import logging

class ReflexosStorage:
    def __init__(self):
        self.logger = logging.getLogger("REFLEXOS_STORAGE")
        
        # Paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.abspath(os.path.join(current_dir, '../../..'))
        self.data_dir = os.path.join(root_dir, "jarvis_system", "data")
        
        self.manual_config = os.path.join(self.data_dir, "reflexos_db", "speech_config.json")
        self.intuition_file = os.path.join(self.data_dir, "intuicao.json")
        
        self._ensure_structure()

    def _ensure_structure(self):
        os.makedirs(os.path.dirname(self.manual_config), exist_ok=True)
        if not os.path.exists(self.manual_config):
            default = {
                "phonetic_corrections": {
                    "freigilson": "Frei Gilson",
                    "freio de o som": "Frei Gilson",
                    "freio gil som": "Frei Gilson",
                    "javas": "Jarvis",
                    "sportfy": "Spotify"
                }
            }
            self.salvar_manual(default["phonetic_corrections"])

    def carregar_manual(self):
        try:
            with open(self.manual_config, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("phonetic_corrections", {})
        except: return {}

    def salvar_manual(self, mapa_correcoes):
        try:
            with open(self.manual_config, 'w', encoding='utf-8') as f:
                json.dump({"phonetic_corrections": mapa_correcoes}, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(f"Erro ao salvar: {e}")
            return False

    def carregar_intuicao(self):
        try:
            if os.path.exists(self.intuition_file):
                with open(self.intuition_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("ruido_ignorado", [])
        except: pass
        return []