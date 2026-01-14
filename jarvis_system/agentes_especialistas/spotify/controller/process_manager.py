import time
import logging
import subprocess
import pyautogui

# Importação condicional
try:
    import win32gui
    import win32process
    WINDOWS = True
except ImportError:
    WINDOWS = False

logger = logging.getLogger("SPOTIFY_PROCESS")

class SpotifyProcessManager:
    """Gerencia o ciclo de vida do processo (Abrir, Fechar, Verificar)."""
    
    def __init__(self, window_manager):
        self.window = window_manager
        self.spotify_path = r"C:\Users\Diogo\AppData\Roaming\Spotify\Spotify.exe"

    def _verificar_janela_existente(self):
        """Verifica se a janela já existe e retorna o HWND."""
        return self.window.obter_hwnd()

    def launch(self):
        """Garante que o Spotify esteja aberto e visível."""
        logger.info("🚀 [Process] Verificando Spotify...")
        
        # 1. Tenta encontrar janela já aberta
        hwnd = self._verificar_janela_existente()
        
        if hwnd:
            logger.info("✅ [Process] Janela detectada. Trazendo para frente.")
            self.window.focar(hwnd)
            return True

        # 2. Se não achou, tenta abrir via comando do Windows (mais robusto que subprocess direto)
        logger.info("⚠️ Janela não encontrada. Iniciando aplicação...")
        try:
            # O comando 'start spotify:' usa o protocolo URI do Windows, funciona independente do caminho do .exe
            subprocess.run("start spotify:", shell=True) 
        except Exception as e:
            logger.error(f"Erro ao lançar processo: {e}")
            return False

        # 3. Loop de espera (Polling)
        for i in range(20): # Espera até 20 segundos (aumentado)
            hwnd = self._verificar_janela_existente()
            if hwnd:
                # --- CORREÇÃO DE WARM-UP ---
                # O Spotify cria a janela antes de carregar o motor de busca (React/Web).
                # Aumentamos de 1.5s para 5.0s para evitar digitar no vazio.
                logger.info("⏳ [Process] Janela detectada. Aguardando renderização da UI (Warm-up)...")
                time.sleep(5.0) 
                
                self.window.focar(hwnd)
                logger.info("✅ [Process] Spotify carregado com sucesso.")
                return True
            
            time.sleep(1)
            if i % 5 == 0: logger.debug("   ...aguardando janela...")

        logger.error("❌ [Process] Timeout. Spotify não abriu ou não criou janela visível.")
        return False