import logging
import time

# Import relativo: Sobe 2 níveis (consciencia -> spotify -> window)
# Ajuste conforme sua estrutura real se necessário
try:
    from ..window import WindowManager
except ImportError:
    # Fallback para testes isolados
    import sys
    print("⚠️ Aviso: Rodando sem WindowManager real (Mock).")
    class WindowManager:
        def obter_hwnd(self): return 12345

logger = logging.getLogger("CONSCIENCIA_PROPRIOC")

class ProprioceptionSystem:
    """
    Sistema de Propriocepção: A capacidade de reconhecer a localização
    e o estado do próprio corpo (neste caso, a janela do App).
    """
    
    def __init__(self, window_manager: WindowManager):
        self.window = window_manager

    def verificar_presenca_app(self) -> bool:
        """Sente se o Spotify está materializado na tela."""
        hwnd = self.window.obter_hwnd()
        existe = hwnd is not None
        
        if not existe:
            logger.debug("👻 Não sinto a presença da janela do Spotify.")
        
        return existe

    def verificar_foco(self) -> bool:
        """
        Verifica se estamos focados na tarefa (Janela ativa).
        Útil para saber se precisamos clicar na janela antes de digitar.
        """
        return self.verificar_presenca_app()