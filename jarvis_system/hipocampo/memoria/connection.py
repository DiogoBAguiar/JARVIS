import logging
import traceback

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

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
        if self.is_connected:
            return self.collection

        if not CHROMA_AVAILABLE:
            self.logger.warning("⚠️ 'chromadb' indisponível. Memória desativada.")
            return None

        try:
            self.client = chromadb.PersistentClient(
                path=self.storage.db_path,
                settings=Settings(
                    allow_reset=True,
                    anonymized_telemetry=False
                )
            )
            
            self.collection = self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
            
            self.is_connected = True
            self.logger.info("✅ Hipocampo conectado ao ChromaDB.")
            return self.collection
            
        except Exception as exc:
            self.is_connected = False
            self.logger.critical(f"🛑 Falha crítica no ChromaDB: {exc}")
            self.logger.debug(traceback.format_exc())
            return None