import json
import os
import logging

class SpatialMemory:
    def __init__(self, app_name="spotify"):
        self.logger = logging.getLogger("SPATIAL_MEMORY")
        self.app_name = app_name
        
        # --- CORREÇÃO DE CAMINHO ---
        # Pega a pasta atual (camera)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Sobe 2 níveis (camera -> cortex_motor -> jarvis_system) e entra em 'data'
        # Estrutura: jarvis_system/cortex_motor/camera/spatial_memory.py
        self.data_dir = os.path.abspath(os.path.join(current_dir, '../../data'))
        
        # Garante que a pasta data existe (segurança)
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir, exist_ok=True)
            
        self.cache_path = os.path.join(self.data_dir, "ui_cache.json")
        # ---------------------------
        
        self.cache = self._carregar_cache()

    def _carregar_cache(self):
        if not os.path.exists(self.cache_path):
            return {}
        try:
            with open(self.cache_path, 'r') as f:
                return json.load(f)
        except Exception:
            return {}

    def _salvar_cache(self):
        try:
            with open(self.cache_path, 'w') as f:
                json.dump(self.cache, f, indent=4)
        except Exception as e:
            self.logger.error(f"Falha ao salvar cache UI: {e}")

    def buscar_coordenada(self, width: int, height: int, elemento: str):
        resolution_key = f"{width}x{height}"
        app_cache = self.cache.get(self.app_name, {})
        res_cache = app_cache.get(resolution_key, {})
        coords = res_cache.get(elemento)
        
        if coords:
            self.logger.info(f"⚡ Memória Espacial: '{elemento}' encontrado em {coords} ({resolution_key})")
            return (coords['x'], coords['y'])
        
        self.logger.info(f"💨 Memória Espacial: '{elemento}' não mapeado para {resolution_key}")
        return None

    def memorizar_coordenada(self, width: int, height: int, elemento: str, x: int, y: int):
        resolution_key = f"{width}x{height}"
        
        if self.app_name not in self.cache:
            self.cache[self.app_name] = {}
            
        if resolution_key not in self.cache[self.app_name]:
            self.cache[self.app_name][resolution_key] = {}
            
        self.cache[self.app_name][resolution_key][elemento] = {"x": int(x), "y": int(y)}
        
        self._salvar_cache()
        self.logger.info(f"💾 Nova coordenada aprendida: '{elemento}' @ {x},{y}")

# Singleton pronto para uso
spatial_mem = SpatialMemory()