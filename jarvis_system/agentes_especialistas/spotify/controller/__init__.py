# Exposição da classe principal para manter compatibilidade com imports antigos
# De: from .controller import SpotifyController
# Para: from .controller import SpotifyController (agora via package)

from .spotify_controller import SpotifyController