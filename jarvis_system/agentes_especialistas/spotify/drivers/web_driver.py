import os
import time
import logging
from playwright.sync_api import sync_playwright

try:
    from .page_model import SpotifyPage
    from .estrategias.search_engine import SearchEngine
    from .scanner import obter_nome_computador 
except ImportError:
    from page_model import SpotifyPage
    from estrategias.search_engine import SearchEngine
    from scanner import obter_nome_computador

logger = logging.getLogger("SPOTIFY_WEB_DRIVER")

class SpotifyWebDriver:
    def __init__(self, headless=True):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.session_dir = os.path.join(self.base_dir, "spotify_web_session")
        # Mantemos Headless=True em prod para poupar GPU/CPU e ser mais rápido
        self.headless = headless
        self.local_device_name = obter_nome_computador()
        logger.info(f"🖥️ [Driver] PC Local: '{self.local_device_name}'")

    def _iniciar_navegador(self, playwright_instance):
        logger.info("🚀 [Driver] Inicializando Microsoft Edge (Nativo)...")
        return playwright_instance.chromium.launch_persistent_context(
            user_data_dir=self.session_dir,
            channel="msedge",
            headless=self.headless,
            args=[
                "--start-maximized", 
                "--disable-blink-features=AutomationControlled"
            ],
            no_viewport=True,
            viewport=None
        )

    def tocar(self, termo_busca: str, tipo: str = "musica", device_name=None) -> bool:
        target_device = device_name if device_name else self.local_device_name
        logger.info(f"🌐 [Fluxo] Iniciando: '{termo_busca}' ({tipo}) -> Em: '{target_device}'")
        
        browser = None
        ja_deu_play = False
        conexao_estabelecida = False # <--- Flag Anti-Redundância

        try:
            with sync_playwright() as p:
                browser = self._iniciar_navegador(p)
                
                if len(browser.pages) > 0: page = browser.pages[0]
                else: page = browser.new_page()
                page.bring_to_front()

                page_model = SpotifyPage(page)
                brain = SearchEngine(page_model)

                # 1. Conexão Inicial
                conexao_estabelecida = page_model.conectar_no_jarvas(target_device)

                # 2. Atalho: "Minhas Músicas"
                termo_lower = termo_busca.lower()
                if termo_lower in ["minhas musicas", "musicas curtidas", "favoritas"]:
                    logger.info("❤️ [Driver] Atalho: Músicas Curtidas")
                    if page_model.tocar_musicas_curtidas():
                        # Só tenta ligar de novo se a primeira tentativa falhou
                        if not conexao_estabelecida:
                            page_model.conectar_no_jarvas(target_device)
                        return True
                    return False

                # 3. Busca
                if not page_model.buscar(termo_busca):
                    logger.error("❌ Falha crítica na busca.")
                    return False

                # 4. Estratégia de Navegação (Rigorosa)
                if "artista" in tipo.lower() or "banda" in tipo.lower():
                    logger.info("🧠 Modo Artista: Ativando navegação profunda...")
                    
                    if not page_model.aplicar_filtro_rigoroso("Artistas"):
                        logger.warning("⚠️ Filtro de Artistas pode ter falhado.")

                    resultado_tab_hunter = page_model.entrar_no_perfil_artista_rigoroso(termo_busca)
                    
                    if not resultado_tab_hunter:
                        logger.error(f"❌ Falha ao acessar perfil exato de '{termo_busca}'.")
                        return False 
                    elif resultado_tab_hunter == "PLAY_DIRETO":
                        ja_deu_play = True 
                else:
                    brain.executar_estrategia(termo_busca, tipo)

                # 5. Play Final
                if ja_deu_play or page_model.tocar_melhor_resultado():
                    logger.info(f"✅ [Sucesso] Play enviado.")
                    
                    # 6. Auditoria de Áudio - REMOÇÃO DE REDUNDÂNCIA
                    # Se não ligou no passo 1, tenta uma última vez agora.
                    if not conexao_estabelecida:
                        page_model.conectar_no_jarvas(target_device)
                    
                    if page_model.validar_reproducao_rigorosa(termo_busca):
                        return True
                    else:
                        logger.error("❌ Validação falhou (Música errada ou Anúncio).")
                        return False
                
                logger.error("❌ Botão Play não encontrado.")
                return False

        except Exception as e:
            logger.error(f"❌ [Erro Crítico] Web Driver falhou: {e}", exc_info=True)
            return False
        
        finally:
            if browser:
                try:
                    logger.info("🔒 [Driver] Encerrando sessão do navegador.")
                    browser.close()
                except: pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    # O default é headless=True (nas sombras)
    driver = SpotifyWebDriver()
    driver.tocar("Matuê", tipo="artista")