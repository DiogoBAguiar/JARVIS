import logging
import difflib
import json
import os
from typing import Optional

# Tenta importar o Curador, mas mantém fallback local se falhar
try:
    from jarvis_system.hipocampo.pensamento_musical import CuradorMusical
except ImportError:
    CuradorMusical = None

logger = logging.getLogger("SPOTIFY_TOOLS")

class SpotifyToolkit:
    """
    Conjunto de ferramentas que a IA pode utilizar.
    Conecta o Cérebro ao Corpo (Controller) e à Memória.
    """

    def __init__(self, controller, consciencia=None):
        self.controller = controller
        self.consciencia = consciencia
        
        # Instancia o Curador Musical se disponível
        self.curador = CuradorMusical() if CuradorMusical else None
        
        # Carrega DB localmente como redundância para garantir a correção
        self.db_artistas = self._carregar_db_artistas_local()
        logger.info("🔧 SpotifyToolkit V3.3 Carregado (Rigor 0.85 + Curador Híbrido)")

    def _carregar_db_artistas_local(self):
        """Carrega DB local para garantir a correção mesmo se o Curador falhar."""
        try:
            path = "jarvis_system/data/reflexos_db/speech_config.json"
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return list(data.get("phonetic_corrections", {}).values())
        except Exception: pass
        return []

    # --- MÉTODOS DE INTELIGÊNCIA ---

    def verificar_se_artista(self, termo: str) -> bool:
        """
        Verifica se o termo é um Artista no banco de dados local.
        """
        # Tenta via Curador primeiro
        if self.curador and hasattr(self.curador, 'existe_artista'):
            return self.curador.existe_artista(termo)
        
        # Fallback local
        if not termo: return False
        return termo.lower() in [a.lower() for a in self.db_artistas]
    
    def sugerir_correcao(self, termo: str) -> Optional[str]:
        """
        Tenta corrigir foneticamente o termo.
        Rigor: 0.85 (BLINDADO contra erros como Fly Me To The Moon -> Walk The Moon)
        """
        # 1. Tenta usar a lista local com ALTO RIGOR
        if self.db_artistas and termo:
            # Cutoff 0.85 é a chave para rejeitar palpites ruins
            matches = difflib.get_close_matches(termo, self.db_artistas, n=1, cutoff=0.85)
            
            if matches:
                sugestao = matches[0]
                # Trava de tamanho
                if abs(len(termo) - len(sugestao)) < 4:
                    logger.info(f"✨ Correção Local Aceita: '{termo}' -> '{sugestao}'")
                    return sugestao
                else:
                    logger.info(f"🛡️ Correção ignorada por tamanho: '{termo}' vs '{sugestao}'")
                    return None

        # 2. Se a local não achou, tenta o Curador (se existir)
        if self.curador:
            return self.curador.sugerir_correcao(termo)

        return None

    # --- MÉTODOS DE AÇÃO (Controller) ---

    def iniciar_aplicativo(self) -> str:
        """Abre o Spotify."""
        try:
            # Compatibilidade com diferentes nomes de método no controller
            if hasattr(self.controller, 'launch_app'):
                self.controller.launch_app()
            elif hasattr(self.controller, 'iniciar_spotify'):
                self.controller.iniciar_spotify()
            return "Spotify iniciado."
        except Exception as e:
            return f"Erro ao abrir: {e}"

    def tocar_musica(self, nome_musica: str, tipo: str = "musica") -> str:
        """
        Toca uma música ou artista específico.
        """
        logger.info(f"🎹 Toolkit tocando: '{nome_musica}' ({tipo})")
        try:
            # Tenta método V2 (play_search)
            if hasattr(self.controller, 'play_search'):
                try:
                    return self.controller.play_search(nome_musica, tipo=tipo)
                except TypeError:
                    return self.controller.play_search(nome_musica)
            
            # Tenta método V1 (navegar_e_tocar)
            elif hasattr(self.controller, 'navegar_e_tocar'):
                self.controller.navegar_e_tocar(nome_musica, tipo)
                return f"Tocando {nome_musica}"
                
            return "Método de toque não encontrado no controller."
        except Exception as e:
            return f"Erro ao tentar tocar: {e}"

    def pausar_ou_continuar(self) -> str:
        if hasattr(self.controller, 'resume'): self.controller.resume()
        elif hasattr(self.controller, 'play_pause'): self.controller.play_pause()
        return "Play/Pause."

    def proxima_faixa(self) -> str:
        if hasattr(self.controller, 'next_track'): self.controller.next_track()
        return "Próxima."

    def faixa_anterior(self) -> str:
        if hasattr(self.controller, 'previous_track'): self.controller.previous_track()
        return "Anterior."

    def consultar_memoria_musical(self, descricao: str) -> str:
        try:
            if self.curador and hasattr(self.curador, 'buscar_vetorial'):
                resultados = self.curador.buscar_vetorial(descricao, top_k=1)
                if resultados:
                    return f"Encontrei na memória: '{resultados[0]}'."
            return "Nada na memória."
        except Exception as e:
            logger.error(f"Erro memória: {e}")
            return "Erro memória."