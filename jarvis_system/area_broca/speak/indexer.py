# jarvis_system/area_broca/speak/indexer.py
import os
import json
import re
from datetime import datetime

class VoiceIndexer:
    def __init__(self, base_dir, logger):
        self.log = logger
        self.base_dir = base_dir
        self.audio_dir = os.path.join(base_dir, "assets")
        self.index_path = os.path.join(base_dir, "voice_index.json")
        self.voice_index = {}
        
        os.makedirs(self.audio_dir, exist_ok=True)
        self.load_index()

    def normalize_key(self, text: str) -> str:
        if not text: return ""
        text = re.sub(r'\([^)]*\)', '', text) 
        text = text.lower()
        trans = str.maketrans("áàãâéêíóõôúç", "aaaaeeiooouc")
        text = text.translate(trans)
        return re.sub(r'[^a-z0-9]', '', text)

    def load_index(self):
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for _, metadata in data.items():
                        chave = metadata.get("key_hash")
                        if chave: self.voice_index[chave] = metadata
                self.log.info(f"📂 Memória Vocal: {len(self.voice_index)} itens.")
            except Exception as e:
                self.log.error(f"Erro índice: {e}")
                self.voice_index = {}

    def save_entry(self, entry: dict):
        current_data = {}
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    current_data = json.load(f)
            except: pass
        
        current_data[entry["key_hash"]] = entry # Usar key_hash como chave principal no JSON é mais seguro para busca
        # Ou manter ID como chave principal se preferir, mas o código antigo usava um mix.
        # Vamos manter o padrão de salvar com a key_hash para lookup rápido.
        
        try:
            with open(self.index_path, 'w', encoding='utf-8') as f:
                json.dump(current_data, f, indent=4, ensure_ascii=False)
            self.voice_index[entry["key_hash"]] = entry
        except: pass

    def get_path(self, key_hash):
        entry = self.voice_index.get(key_hash)
        if entry:
            path = entry.get("file_path", "").replace("/", os.sep).replace("\\", os.sep)
            full_path = os.path.join(self.base_dir, path)
            if os.path.exists(full_path):
                return full_path, entry
        return None, None

    def determine_category(self, text):
        key = self.normalize_key(text)
        if key in self.voice_index:
            return self.voice_index[key].get("category", "GENERICO")
        
        t = text.lower()
        if "erro" in t or "falha" in t: return "ALERTA"
        if "bom dia" in t or "boa noite" in t: return "BOAS_VINDAS"
        if "online" in t: return "BOAS_VINDAS"
        if "status" in t: return "STATUS"
        return "GENERICO"

    def detect_context_temporal(self, text):
        t = text.lower()
        if "bom dia" in t: return "morning"
        if "boa tarde" in t: return "afternoon"
        if "boa noite" in t: return "night"
        h = datetime.now().hour
        return "morning" if 5<=h<12 else "afternoon" if 12<=h<18 else "night"

    def detect_sub_context(self, text, category):
        # Lógica simplificada, pode expandir
        if category == "ALERTA": return "alert"
        if "?" in text: return "query"
        return "passive"

    def generate_next_id(self, category):
        # Lógica simplificada de ID
        # Idealmente leria o JSON para achar o max ID
        # Aqui vamos usar timestamp curto para evitar IO excessivo
        return f"{category.lower()}_{int(datetime.now().timestamp())}"