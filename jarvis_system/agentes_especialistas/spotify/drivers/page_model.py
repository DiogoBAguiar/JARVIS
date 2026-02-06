from playwright.sync_api import Page

# --- CORREÇÃO DE IMPORTAÇÃO (Híbrida) ---
try:
    # Tenta importar como módulo do pacote (J.A.R.V.I.S.)
    from .spotify_nav import SpotifyNavMixin
    from .spotify_content import SpotifyContentMixin
    from .spotify_player import SpotifyPlayerMixin
except ImportError:
    # Fallback para rodar como script isolado (Teste)
    from spotify_nav import SpotifyNavMixin
    from spotify_content import SpotifyContentMixin
    from spotify_player import SpotifyPlayerMixin

class SpotifyPage(SpotifyNavMixin, SpotifyContentMixin, SpotifyPlayerMixin):
    """
    FACADE PRINCIPAL DO SPOTIFY
    Herda comportamentos de:
    - Navegação (Busca, URL)
    - Conteúdo (Filtros, Perfil)
    - Player (Play, Pause, Dispositivos)
    """

    def __init__(self, page: Page):
        self.page = page