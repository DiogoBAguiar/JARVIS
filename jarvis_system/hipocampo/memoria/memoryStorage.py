import os
import logging

class MemoryStorage:
    def __init__(self):
        self.logger = logging.getLogger("HIPOCAMPUS_STORAGE")
        
        # Caminhos Absolutos
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        # Sobe 3 níveis: memoria -> hipocampo -> jarvis_system -> Raiz
        self.root_dir = os.path.abspath(os.path.join(self.current_dir, '../../..'))
        
        # Onde o banco físico vive
        self.db_path = os.path.join(self.root_dir, "jarvis_system", "data", "jarvis_memory_db")
        
        self._ensure_paths()

    def _ensure_paths(self):
        """Garante que a estrutura física exista."""
        if not os.path.exists(self.db_path):
            try:
                os.makedirs(self.db_path, exist_ok=True)
                self.logger.info(f"📁 Diretório de memória criado em: {self.db_path}")
            except Exception as e:
                self.logger.critical(f"❌ Erro crítico ao criar diretório do DB: {e}")