import json
import logging
import tempfile
import shutil
import os
from pathlib import Path
from typing import Dict, List, Any

class ReflexosStorage:
    def __init__(self):
        self.logger = logging.getLogger("REFLEXOS_STORAGE")
        
        self.current_dir = Path(__file__).resolve().parent
        self.root_dir = self.current_dir.parent.parent.parent
        self.data_dir = self.root_dir / "jarvis_system" / "data"
        self.reflexos_db_dir = self.data_dir / "reflexos_db"
        
        self.manual_config_path = self.reflexos_db_dir / "speech_config.json"
        self.intuition_path = self.data_dir / "intuicao.json"
        
        self._ensure_structure()

    def _ensure_structure(self):
        try:
            self.reflexos_db_dir.mkdir(parents=True, exist_ok=True)
            
            # Dicionário Limpo e Otimizado
            default_map = {
                "freigilson": "Frei Gilson",
                "freio de o som": "Frei Gilson",
                "freio gil som": "Frei Gilson",
                "javas": "Jarvis",
                "jarbas": "Jarvis",
                "sportfy": "Spotify",
                "code play": "Coldplay",
                "cold play": "Coldplay",
                "com o de play": "Coldplay"
            }

            # Se arquivo não existe, cria novo
            if not self.manual_config_path.exists():
                self.salvar_manual(default_map)
            else:
                # MANUTENÇÃO AUTOMÁTICA: Remove regras perigosas existentes
                current = self.carregar_manual()
                changed = False
                
                # Lista negra de regras que causam loop (ex: toc -> tocar)
                blacklist = ["toc", "play", "som"] 
                
                for bad_key in blacklist:
                    if bad_key in current:
                        del current[bad_key]
                        changed = True
                        self.logger.warning(f"🧹 Regra perigosa removida automaticamente: '{bad_key}'")
                
                # Garante que Coldplay esteja lá
                if "code play" not in current:
                    current["code play"] = "Coldplay"
                    changed = True
                
                if changed:
                    self.salvar_manual(current)

        except Exception as e:
            self.logger.error(f"Erro estrutura: {e}")

    def _load_json(self, path: Path, default: Any) -> Any:
        if not path.exists(): return default
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return default

    def carregar_manual(self) -> Dict[str, str]:
        data = self._load_json(self.manual_config_path, {})
        return data.get("phonetic_corrections", {})

    def carregar_intuicao(self) -> List[str]:
        data = self._load_json(self.intuition_path, {})
        return data.get("ruido_ignorado", [])

    def _atomic_write(self, path: Path, data: dict) -> bool:
        try:
            dir_name = path.parent
            with tempfile.NamedTemporaryFile('w', delete=False, dir=dir_name, encoding='utf-8') as tmp_file:
                json.dump(data, tmp_file, indent=4, ensure_ascii=False)
                temp_path = Path(tmp_file.name)
            shutil.move(str(temp_path), str(path))
            return True
        except Exception: return False

    def salvar_manual(self, mapa_correcoes: Dict[str, str]) -> bool:
        return self._atomic_write(self.manual_config_path, {"phonetic_corrections": mapa_correcoes})

    def salvar_intuicao(self, lista_ignorados: List[str]) -> bool:
        lista_limpa = sorted(list(set(lista_ignorados)))
        return self._atomic_write(self.intuition_path, {"ruido_ignorado": lista_limpa})