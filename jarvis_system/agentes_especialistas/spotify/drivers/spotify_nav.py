import time
import logging

# Importação Defensiva
try:
    from .spotify_selectors import SpotifySelectors as S
except ImportError:
    from spotify_selectors import SpotifySelectors as S

logger = logging.getLogger("SPOTIFY_NAV")

class SpotifyNavMixin:
    """Mixin responsável apenas por buscar e navegar (Blindado contra Layout Responsivo)."""
    
    def ir_para_busca(self):
        """
        Garante que o campo de busca esteja visível.
        Se não estiver, clica na Lupa ou navega via URL.
        """
        # 1. Tenta verificar se já estamos na URL certa
        if "/search" not in self.page.url:
            logger.info("📍 Navegando direto para área de busca...")
            self.page.goto("https://open.spotify.com/search")
            time.sleep(2) # Espera carregar

        # 2. Verifica se o Input já está visível
        try:
            self.page.wait_for_selector(S.SEL_BUSCA_INPUT, state="visible", timeout=3000)
            return # Se achou, ótimo
        except:
            logger.warning("⚠️ Input de busca não visível. Tentando abrir via ícone...")

        # 3. Se não achou, Clica no Ícone da Lupa (Layout Responsivo/Mobile)
        try:
            lupa = self.page.locator(S.SEL_BUSCA_ABRIR).first
            if lupa.is_visible():
                lupa.click(force=True)
                # Agora espera o input aparecer obrigatoriamente
                self.page.wait_for_selector(S.SEL_BUSCA_INPUT, state="visible", timeout=5000)
            else:
                logger.error("❌ Nem o input nem a lupa foram encontrados.")
        except Exception as e:
            logger.error(f"❌ Falha ao tentar abrir busca: {e}")

    def buscar(self, termo: str) -> bool:
        """Digita o termo na barra e pressiona ENTER."""
        # Garante que estamos no lugar certo antes de digitar
        self.ir_para_busca()
        
        try:
            inp = self.page.locator(S.SEL_BUSCA_INPUT)
            inp.wait_for(state="visible", timeout=5000)
            inp.click(force=True)
            inp.fill("")
            inp.type(termo, delay=50)
            logger.info(f"⌨️ Digitado: '{termo}'. Enter...")
            inp.press("Enter")
            time.sleep(2.5) 
            return True
        except Exception as e:
            logger.error(f"❌ Erro na busca: {e}")
            return False