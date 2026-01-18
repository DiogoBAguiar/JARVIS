import uuid
import datetime
import re
import logging
from typing import Optional, Dict, Any, List

from .storage import MemoryStorage
from .connection import ChromaConnection

class MemoriaHipocampo:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("HIPOCAMPO_CORE")
        
        self.storage = MemoryStorage()
        self.connection_manager = ChromaConnection(self.storage)
        
        # Propriedades de compatibilidade
        self.db_path = self.storage.db_path
        self.collection = None
        
        # Auto-conectar
        self._conectar()

    def _conectar(self):
        self.collection = self.connection_manager.connect()
        return self.collection is not None

    # =======================
    # Utilitários
    # =======================
    def _normalizar(self, texto: str, limite: int = 20) -> str:
        return re.sub(r"[^a-zA-Z0-9]", "", texto).lower()[:limite]

    def _gerar_id_track(self, musica: str, artista: str) -> str:
        return (
            f"tk_"
            f"{self._normalizar(musica)}_"
            f"{self._normalizar(artista)}_"
            f"{uuid.uuid4().hex[:4]}"
        )

    # =======================
    # Memória Genérica (Compatibilidade Brain LLM)
    # =======================
    def memorizar(self, fato: str) -> bool:
        """
        Método genérico para salvar fatos ensinados pelo usuário.
        Ex: 'Gosto de azul', 'Meu nome é Diogo'.
        """
        if not self._conectar(): return False

        timestamp = datetime.datetime.utcnow().isoformat()
        
        try:
            doc_id = f"fact_{uuid.uuid4().hex[:8]}"
            self.collection.add(
                documents=[fato],
                metadatas=[{"timestamp": timestamp, "tipo": "fato_usuario"}],
                ids=[doc_id]
            )
            self.logger.info(f"💾 Fato memorizado: '{fato}'")
            return True
        except Exception as exc:
            self.logger.error(f"❌ Erro ao memorizar fato: {exc}")
            return False

    # Aliases para compatibilidade com versões antigas do Cérebro
    def adicionar_memoria(self, fato: str): return self.memorizar(fato)
    def gravar(self, fato: str): return self.memorizar(fato)

    # =======================
    # Memória Musical
    # =======================
    def memorizar_musica(self, musica: str, artista: str, tags: str = "spotify_likes", extra_info: Optional[Dict[str, Any]] = None):
        if not self._conectar(): return

        tags = tags.lower().strip()
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
            self.logger.info(f"💾 Memória musical consolidada: {musica} — {artista}")
        except Exception as exc:
            self.logger.error(f"❌ Erro ao persistir música: {exc}")

    # =======================
    # Memória Episódica (Experiências dos Agentes)
    # =======================
    def memorizar_episodio(self, agente: str, acao: str, resultado: str, emocao_associada: str, detalhes: str = ""):
        """
        Armazena uma experiência vivida por um agente.
        """
        if not self._conectar(): return

        timestamp = datetime.datetime.utcnow().isoformat()
        documento = (
            f"Episódio do agente {agente}: Tentativa de '{acao}'. "
            f"Resultado: {resultado}. O agente sentiu-se {emocao_associada}. "
            f"Detalhes: {detalhes}"
        )

        metadados = {
            "tipo": "episodio_agente",
            "agente": agente,
            "acao": acao,
            "resultado": resultado,
            "emocao": emocao_associada,
            "timestamp": timestamp
        }

        try:
            evento_id = f"evt_{agente}_{uuid.uuid4().hex[:8]}"
            self.collection.add(
                documents=[documento],
                metadatas=[metadados],
                ids=[evento_id]
            )
            self.logger.info(f"🧠 Memória episódica gravada: {agente} -> {acao} ({resultado})")
        except Exception as exc:
            self.logger.error(f"❌ Erro ao gravar episódio: {exc}")

    # =======================
    # Recuperação
    # =======================
    def relembrar(self, consulta: str, limite: int = 3, tags: Optional[str] = None) -> str:
        """
        Busca memórias. Retorna STRING formatada (compatibilidade com LLM).
        """
        if not self._conectar() or not consulta.strip(): return ""

        try:
            if tags: tags = tags.lower().strip()
            filtro = {"tags": tags} if tags else None

            resultado = self.collection.query(
                query_texts=[consulta],
                n_results=limite,
                where=filtro
            )
            
            # O Chroma retorna uma lista de listas. Pegamos a primeira lista.
            documentos = resultado.get("documents", [])
            if documentos and len(documentos) > 0:
                lista_docs = documentos[0]
                # Formata para o LLM consumir como texto
                return "\n".join([f"- {d}" for d in lista_docs if d])
            
            return ""
        except Exception as exc:
            self.logger.error(f"❌ Falha na recuperação: {exc}")
            return ""

    def consultar_experiencia_passada(self, agente: str, acao: str) -> List[str]:
        """Consulta experiências passadas de falhas ou erros."""
        if not self._conectar(): return []
        query = f"experiência {agente} executando {acao} falha erro frustração"
        # Aqui retornamos lista bruta se precisar de processamento interno
        res = self.relembrar(query, limite=2)
        return res.split("\n") if res else []

    def status(self) -> str:
        if not self.connection_manager.is_connected:
            return "Offline"
        return f"Online ({self.collection.count()} registros)"