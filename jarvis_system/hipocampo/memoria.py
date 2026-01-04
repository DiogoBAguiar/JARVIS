import chromadb
import uuid
import os
from datetime import datetime
from jarvis_system.cortex_frontal.observability import JarvisLogger

log = JarvisLogger("HIPOCAMPO_MEMORIA")

class Hipocampo:
    def __init__(self):
        # Define o caminho do banco para ficar dentro da pasta do projeto
        db_path = os.path.join(os.getcwd(), "jarvis_memory_db")
        
        # Cliente persistente (salva no disco)
        # O Chroma baixa automaticamente um modelo leve (all-MiniLM-L6-v2) na primeira vez
        try:
            self.client = chromadb.PersistentClient(path=db_path)
            
            # Coleção de memórias episódicas (Fatos sobre você)
            self.episodica = self.client.get_or_create_collection(name="episodic_memory")
            
            qtd_memorias = self.episodica.count()
            log.info(f"Sistema Límbico conectado. {qtd_memorias} memórias acessíveis.")
        except Exception as e:
            log.critical(f"ERRO CRÍTICO AO INICIAR MEMÓRIA: {e}")
            raise e

    def memorizar(self, texto: str, tags: str = "fato"):
        """
        Consolida uma memória de curto prazo em longo prazo.
        """
        log.info(f"Consolidando no hipocampo: '{texto}'")
        
        try:
            self.episodica.add(
                documents=[texto],
                metadatas=[{"timestamp": str(datetime.now()), "tags": tags}],
                ids=[str(uuid.uuid4())]
            )
            return "Memória consolidada com sucesso."
        except Exception as e:
            log.error(f"Erro de gravação: {e}")
            return "Falha ao gravar memória."

    def relembrar(self, consulta: str, n_resultados: int = 2) -> str:
        """
        Recupera memórias associativas baseadas no contexto (Busca Semântica).
        """
        try:
            # 1. Se o cérebro está vazio, não perca tempo buscando
            if self.episodica.count() == 0:
                return ""

            # 2. Busca Semântica
            results = self.episodica.query(
                query_texts=[consulta],
                n_results=n_resultados
            )
            
            # Extrai os documentos encontrados (lista de listas)
            memorias_encontradas = results['documents'][0]
            
            if not memorias_encontradas:
                return ""
            
            # 3. Formata para o Cérebro ler de forma organizada
            # Adiciona um marcador visual para a LLM entender que isso é passado
            contexto = "\n".join([f"- [MEMÓRIA]: {m}" for m in memorias_encontradas])
            
            log.info(f"Memória ativada para '{consulta}': {len(memorias_encontradas)} fatos recuperados.")
            return contexto
            
        except Exception as e:
            log.error(f"Falha na recuperação de memória: {e}")
            return ""

    def esquecer_tudo(self):
        """DANGER: Reseta a memória (Útil para testes)"""
        try:
            self.client.delete_collection("episodic_memory")
            self.episodica = self.client.get_or_create_collection(name="episodic_memory")
            log.warning("Todas as memórias foram apagadas.")
            return "Memória formatada."
        except Exception as e:
            return f"Erro ao apagar: {e}"

# Instância exportada (Singleton)
memoria = Hipocampo()