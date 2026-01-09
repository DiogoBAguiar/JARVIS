import os
import uuid
import datetime
import re
import traceback
from typing import Optional, Dict, Any, List

from jarvis_system.cortex_frontal.observability import JarvisLogger

log = JarvisLogger("HIPOCAMPO")

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    log.warning("⚠️ 'chromadb' indisponível. Subsistema de memória desativado.")


class Hipocampo:
    """
    Subsistema de Memória Vetorial Semântica.
    Responsável apenas por:
    - Persistência
    - Recuperação
    - Estado de conexão
    """

    COLLECTION_NAME = "jarvis_knowledge_base"

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or self._resolver_caminho_db()
        self.client: Optional["chromadb.PersistentClient"] = None
        self.collection: Optional["chromadb.Collection"] = None
        self._is_connected: bool = False

    # =======================
    # Infraestrutura
    # =======================

    @staticmethod
    def _resolver_caminho_db() -> str:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base, "data", "jarvis_memory_db")

    def _conectar(self) -> bool:
        if self._is_connected:
            return True

        if not CHROMA_AVAILABLE:
            return False

        try:
            os.makedirs(self.db_path, exist_ok=True)

            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=Settings(
                    allow_reset=True,
                    anonymized_telemetry=False
                )
            )

            self.collection = self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )

            self._is_connected = True
            log.info("✅ Hipocampo conectado ao ChromaDB.")
            return True

        except Exception as exc:
            self._is_connected = False
            log.critical(
                f"🛑 Falha crítica ao inicializar ChromaDB: {type(exc).__name__} - {exc}"
            )
            log.debug(traceback.format_exc())
            return False

    # =======================
    # Normalização & IDs
    # =======================

    @staticmethod
    def _normalizar(texto: str, limite: int = 20) -> str:
        return re.sub(r"[^a-zA-Z0-9]", "", texto).lower()[:limite]

    def _gerar_id_track(self, musica: str, artista: str) -> str:
        return (
            f"tk_"
            f"{self._normalizar(musica)}_"
            f"{self._normalizar(artista)}_"
            f"{uuid.uuid4().hex[:4]}"
        )

    # =======================
    # Escrita
    # =======================

    def memorizar_musica(
        self,
        musica: str,
        artista: str,
        tags: str = "spotify_likes",
        extra_info: Optional[Dict[str, Any]] = None
    ) -> None:
        if not self._conectar():
            return

        # --- 🛡️ VACINA DE NORMALIZAÇÃO ---
        # Converte a tag para minúsculo antes de salvar (Ex: "Acadus" -> "acadus")
        tags = tags.lower().strip()
        # -------------------------------

        info = extra_info or {}

        documento = f"Preferência musical registrada: {musica}, de {artista}."

        metadados = {
            "musica": musica,
            "artista": artista,
            "tags": tags,
            "spotify_id": str(info.get("id", "manual")),
            "explicit": bool(info.get("explicit", False)),
            "tipo": "track",
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

        try:
            self.collection.upsert(
                documents=[documento],
                metadatas=[metadados],
                ids=[self._gerar_id_track(musica, artista)]
            )
            log.info(f"💾 Memória musical consolidada: {musica} — {artista} [{tags}]")

        except Exception as exc:
            log.error(
                f"❌ Erro ao persistir memória musical: {type(exc).__name__} - {exc}"
            )

    # =======================
    # Leitura
    # =======================

    def relembrar(
        self,
        consulta: str,
        limite: int = 3,
        tags: Optional[str] = None
    ) -> List[str]:
        if not self._conectar() or not consulta.strip():
            return []

        try:
            # --- 🛡️ VACINA DE NORMALIZAÇÃO ---
            # Garante que a busca também use minúsculas
            if tags:
                tags = tags.lower().strip()
            # -------------------------------

            filtro = {"tags": tags} if tags else None

            resultado = self.collection.query(
                query_texts=[consulta],
                n_results=limite,
                where=filtro
            )

            documentos = resultado.get("documents", [[]])[0]
            return [doc for doc in documentos if doc]

        except Exception as exc:
            log.error(f"❌ Falha na recuperação semântica: {exc}")
            return []

    # =======================
    # Status
    # =======================

    def status(self) -> str:
        if not self._is_connected:
            return "Offline (memória ainda não inicializada)"
        return f"Online ({self.collection.count()} registros)"


# Singleton explícito (decisão consciente)
memoria = Hipocampo()