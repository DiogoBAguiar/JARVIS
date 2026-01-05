import os
import uuid
import datetime
from typing import List, Optional

# Logging do Sistema
from jarvis_system.cortex_frontal.observability import JarvisLogger

log = JarvisLogger("HIPOCAMPO")

# Tentativa de importação segura do ChromaDB
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    log.warning("⚠️ Biblioteca 'chromadb' não encontrada. Memória desativada.")
    CHROMA_AVAILABLE = False

class Hipocampo:
    def __init__(self):
        # Configuração de Caminho: Garante que o DB fique na raiz do projeto
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.db_path = os.path.join(base_dir, "data", "jarvis_memory_db")
        
        self.client = None
        self.collection = None
        self._is_connected = False

    def _conectar(self) -> bool:
        """
        Lazy Connection: Só conecta quando necessário.
        Retorna True se conectado com sucesso.
        """
        if self._is_connected: return True
        if not CHROMA_AVAILABLE: return False

        log.info("🔌 Conectando ao Hipocampo (ChromaDB)...")
        try:
            os.makedirs(self.db_path, exist_ok=True)

            # --- CORREÇÃO DO TYPO AQUI ---
            # De: anonnymized_telemetry (Errado)
            # Para: anonymized_telemetry (Correto)
            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=Settings(allow_reset=True, anonymized_telemetry=False)
            )
            
            self.collection = self.client.get_or_create_collection(
                name="episodic_memory",
                metadata={"hnsw:space": "cosine"}
            )
            
            self._is_connected = True
            log.info(f"✅ Memória carregada. {self.collection.count()} registros ativos.")
            return True
        except Exception as e:
            # Captura erro, mas não crita o programa inteiro, apenas desativa a memória
            log.critical(f"🛑 FATAL: ❌ Falha crítica no ChromaDB: {e}")
            return False

    def memorizar(self, texto: str, tags: str = "fato_geral") -> str:
        """Adiciona nova memória de longo prazo."""
        if not self._conectar():
            return "Erro: Sistema de memória indisponível."

        log.info(f"💾 Consolidando: '{texto}'")
        try:
            self.collection.add(
                documents=[texto],
                metadatas=[{
                    "timestamp": datetime.datetime.now().isoformat(),
                    "source": "user_interaction",
                    "tags": tags
                }],
                ids=[str(uuid.uuid4())]
            )
            return "Memória consolidada."
        except Exception as e:
            log.error(f"Erro de gravação: {e}")
            return "Falha na gravação."

    def relembrar(self, query: str, limit: int = 3) -> str:
        """Recupera contexto relevante."""
        if not self._conectar(): return ""
        if not query.strip(): return ""

        try:
            if self.collection.count() == 0: return ""

            results = self.collection.query(
                query_texts=[query],
                n_results=limit
            )

            docs = results.get('documents', [[]])[0]
            
            if not docs: 
                return ""

            formatted_memories = [f"- {doc}" for doc in docs]
            contexto = "\n".join(formatted_memories)
            
            log.debug(f"🧠 Flashback ({len(docs)}): {contexto[:50]}...")
            return contexto

        except Exception as e:
            log.error(f"Erro de leitura: {e}")
            return ""

    def status(self) -> str:
        if not self._conectar(): return "Offline"
        return f"Online ({self.collection.count()} memórias)"

memoria = Hipocampo()