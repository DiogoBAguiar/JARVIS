import sys
import os

# Imports dos módulos
from .musicSearchEngine import MusicSearchEngine
from .musicMaintenance import MusicMaintenance
from .musicEnrichment import MusicEnrichment
from .musicReporter import MusicReporter

# Importação da memória (mantida)
try:
    from jarvis_system.hipocampo.memoria import memoria
except ImportError:
    memoria = None

class CuradorMusical:
    """
    Fachada (Facade) para o sistema de pensamento musical.
    Centraliza o acesso aos módulos de busca, manutenção e enriquecimento.
    """
    def __init__(self):
        self.collection = None
        if memoria and memoria._conectar():
            self.collection = memoria.collection
        
        # Inicializa os sub-módulos injetando a coleção
        self.search_engine = MusicSearchEngine(self.collection, self._log)
        self.maintenance = MusicMaintenance(self.collection, self._log)
        self.enrichment = MusicEnrichment(self.collection, self._log)
        self.reporter = MusicReporter(self.collection, self._log)

    def _log(self, msg):
        print(f"   [CURADOR] {msg}")

    # --- MÉTODOS DE BUSCA (Delegados para SearchEngine) ---
    def existe_artista(self, nome: str) -> bool:
        return self.search_engine.existe_artista(nome)

    def buscar_vetorial(self, query: str, top_k: int = 1) -> list:
        return self.search_engine.buscar_vetorial(query, top_k)

    def tocar_dj(self, comando):
        print(f"\n🎧 [DJ JARVIS] Buscando: '{comando}'")
        res = self.buscar_vetorial(comando, top_k=1)
        if res: self._log(f"Sugestão: {res[0]}")
        else: self._log("Nada encontrado.")

    # --- MÉTODOS DE MANUTENÇÃO (Delegados para Maintenance) ---
    def remover_lixo(self):
        self.maintenance.remover_lixo()

    def refinar_generos(self):
        self.maintenance.refinar_generos()

    def aplicar_patch_manual(self):
        self.maintenance.aplicar_patch_manual()

    # --- MÉTODOS DE ENRIQUECIMENTO (Delegados para Enrichment) ---
    def buscar_anos_faltantes(self):
        self.enrichment.buscar_anos_faltantes()

    # --- RELATÓRIOS (Delegados para Reporter) ---
    def gerar_relatorio(self):
        self.reporter.gerar_relatorio()
    
    def sugerir_correcao(self, termo):
        return self.search_engine.sugerir_correcao(termo)