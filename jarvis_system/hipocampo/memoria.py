import chromadb
import uuid
import os
from datetime import datetime
from jarvis_system.cortex_frontal.observability import JarvisLogger

log = JarvisLogger("HIPOCAMPO_MEMORIA")

class Hipocampo:
    def __init__(self):
        # Define o caminho do banco para ficar dentro da pasta hipocampo ou na raiz
        db_path = os.path.join(os.getcwd(), "jarvis_memory_db")
        
        # Cliente persistente (salva no disco)
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Coleção de memórias episódicas (Fatos sobre você)
        self.episodica = self.client.get_or_create_collection(name="episodic_memory")
        log.info("Sistema Límbico (Memória) conectado.")

    def memorizar(self, texto: str, tags: str = "fato"):
        """
        Consolida uma memória de curto prazo em longo prazo.
        """
        log.info(f"Consolidando no hipocampo: '{texto}'")
        
        self.episodica.add(
            documents=[texto],
            metadatas=[{"timestamp": str(datetime.now()), "tags": tags}],
            ids=[str(uuid.uuid4())]
        )
        return "Memória consolidada."

    def relembrar(self, consulta: str, n_resultados: int = 2) -> str:
        """
        Recupera memórias associativas baseadas no contexto (Busca Semântica).
        """
        try:
            results = self.episodica.query(
                query_texts=[consulta],
                n_results=n_resultados
            )
            
            # Extrai os documentos encontrados
            memorias_encontradas = results['documents'][0]
            
            if not memorias_encontradas:
                return ""
            
            # Formata para o Cérebro ler
            contexto = "\n".join([f"- [Lembrança]: {m}" for m in memorias_encontradas])
            log.info(f"Memória ativada para '{consulta}': {len(memorias_encontradas)} fatos.")
            return contexto
            
        except Exception as e:
            log.error(f"Falha na recuperação de memória: {e}")
            return ""

# Instância exportada
memoria = Hipocampo()