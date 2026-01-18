import logging
import traceback
import os

try:
    import chromadb
    # Tenta importar Settings da nova localização, se falhar, usa a antiga ou dict
    try:
        from chromadb.config import Settings
    except ImportError:
        from chromadb import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    Settings = None

class ChromaConnection:
    COLLECTION_NAME = "jarvis_knowledge_base"

    def __init__(self, storage):
        self.storage = storage
        self.logger = logging.getLogger("HIPOCAMPUS_CONN")
        self.client = None
        self.collection = None
        self.is_connected = False

    def connect(self):
        """Estabelece a conexão e retorna a coleção."""
        if self.is_connected and self.collection:
            return self.collection

        if not CHROMA_AVAILABLE:
            self.logger.warning("⚠️ 'chromadb' indisponível. Memória desativada.")
            return None

        try:
            # Garante que o caminho existe antes de tentar conectar
            if not os.path.exists(self.storage.db_path):
                os.makedirs(self.storage.db_path, exist_ok=True)

            self.logger.info(f"🔌 Conectando ao ChromaDB em: {self.storage.db_path}")

            # Instancia o Cliente Persistente
            # Configuração otimizada para evitar telemetria e permitir reset
            self.client = chromadb.PersistentClient(
                path=self.storage.db_path,
                settings=Settings(
                    allow_reset=True,
                    anonymized_telemetry=False
                )
            )
            
            # Obtém ou cria a coleção (Knowledge Base)
            self.collection = self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"} # Distância de cosseno é melhor para texto
            )
            
            self.is_connected = True
            self.logger.info("✅ Hipocampo conectado ao ChromaDB com sucesso.")
            return self.collection
            
        except Exception as exc:
            self.is_connected = False
            self.logger.critical(f"🛑 Falha crítica no ChromaDB: {exc}")
            # Log detalhado apenas se estiver em debug, para não poluir o console
            self.logger.debug(traceback.format_exc())
            return None