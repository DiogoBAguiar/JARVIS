import time
import logging
import subprocess

# Importação relativa: sobe um nível (..) para acessar window.py
from ..window import WindowManager

logger = logging.getLogger("SPOTIFY_PROCESS")

class SpotifyProcessManager:
    """
    Especialista em Processos do SO.
    Responsabilidade: Garantir que o Spotify esteja rodando e com janela visível.
    """
    
    def __init__(self, window_manager: WindowManager):
        self.window = window_manager

    def launch(self, timeout: int = 15) -> bool:
        """
        Inicia o processo via protocolo 'spotify:' e aguarda a janela aparecer.
        
        Args:
            timeout (int): Tempo máximo de espera em segundos.
            
        Returns:
            bool: True se a janela foi detectada, False se houve timeout.
        """
        logger.info("🚀 [Process] Iniciando Spotify...")
        try:
            # O comando 'start' do Windows é não-bloqueante e usa a associação de arquivo
            subprocess.run("start spotify:", shell=True)
            
            # Loop de espera ativa (Polling)
            start_time = time.time()
            while time.time() - start_time < timeout:
                # Verifica se a janela existe
                if self.window.obter_hwnd():
                    logger.info("✅ [Process] Janela detectada e pronta.")
                    time.sleep(1.5) # Tempo extra para a UI renderizar totalmente
                    return True
                time.sleep(1) # Verifica a cada 1 segundo
            
            logger.error(f"❌ [Process] Timeout ({timeout}s). Spotify não abriu.")
            return False

        except Exception as e:
            logger.error(f"❌ [Process] Erro crítico ao iniciar processo: {e}")
            return False