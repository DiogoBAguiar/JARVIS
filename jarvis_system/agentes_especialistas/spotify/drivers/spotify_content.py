import time
import logging

try:
    from .spotify_selectors import SpotifySelectors as S
except ImportError:
    from spotify_selectors import SpotifySelectors as S

logger = logging.getLogger("SPOTIFY_CONTENT")

class SpotifyContentMixin:
    """Mixin responsável por interagir com filtros, perfis e listas."""

    def aplicar_filtro(self, nome_filtro: str):
        try:
            chip = self.page.locator(f'{S.SEL_FILTRO_CHIP}:has-text("{nome_filtro}")').first
            if chip.is_visible():
                chip.click()
                time.sleep(1.5)
                return True
        except: pass
        return False

    def entrar_no_perfil_artista(self, nome_alvo: str = None) -> bool:
        # Garante que retorne um booleano para quem usar o método antigo
        return bool(self.entrar_no_perfil_artista_rigoroso(nome_alvo))

    # =========================================================================
    # MÉTODOS RIGOROSOS (TAB HUNTER - LÓGICA DE PLAY DIRETO)
    # =========================================================================

    def aplicar_filtro_rigoroso(self, nome_filtro: str) -> bool:
        try:
            chip = self.page.locator(f'{S.SEL_FILTRO_CHIP}:has-text("{nome_filtro}")').first
            if chip.is_visible():
                if chip.get_attribute("aria-checked") == "true":
                    logger.info(f"✅ Filtro '{nome_filtro}' já estava ativo.")
                    return True
                
                chip.evaluate("e => e.click()")
                time.sleep(2.0)
                
                if chip.get_attribute("aria-checked") == "true":
                    logger.info(f"✅ Filtro '{nome_filtro}' confirmado ativo.")
                    return True
        except: pass
        return False

    def entrar_no_perfil_artista_rigoroso(self, nome_alvo: str):
        """
        Retorna:
        "PLAY_DIRETO" -> Deu play na lista de busca.
        "PERFIL_ABERTO" -> Abriu a página do artista.
        False -> Falhou.
        """
        logger.info(f"🧐 [Auditoria] Iniciando TAB HUNTER para: '{nome_alvo}'...")
        
        try:
            try:
                self.page.locator(S.SEL_AREA_PRINCIPAL).click(position={"x": 10, "y": 10}, force=True)
            except:
                self.page.mouse.click(0, 0)
                
            time.sleep(0.5)

            max_tabs = 50 
            encontrou = False
            play_direto = False
            
            for i in range(max_tabs):
                self.page.keyboard.press("Tab")
                texto_focado = self.page.evaluate("document.activeElement.innerText || document.activeElement.getAttribute('aria-label') || ''")
                texto_focado_lower = texto_focado.lower()
                alvo_lower = nome_alvo.lower()

                if ("tocar" in texto_focado_lower or "play" in texto_focado_lower) and alvo_lower in texto_focado_lower:
                    logger.info(f"▶️ ALVO 'PLAY' LOCALIZADO no Tab {i+1}! Texto: '{texto_focado}'")
                    play_direto = True
                    encontrou = True
                    break
                
                elif alvo_lower == texto_focado_lower or alvo_lower in texto_focado_lower:
                    logger.info(f"👤 ALVO 'PERFIL' LOCALIZADO no Tab {i+1}! Texto: '{texto_focado}'")
                    encontrou = True
                    break
                
                time.sleep(0.05)

            if not encontrou:
                logger.error(f"❌ Não encontrei '{nome_alvo}' após {max_tabs} Tabs.")
                return False

            logger.info("⚡ Pressionando ENTER no alvo focado...")
            self.page.keyboard.press("Enter")
            time.sleep(2.0)

            if play_direto:
                logger.info("🎉 Play acionado diretamente na lista! Pulando verificação de perfil.")
                return "PLAY_DIRETO" # <--- MUDANÇA AQUI
            else:
                logger.info("⏳ Aguardando navegação para perfil...")
                try:
                    self.page.wait_for_url("**/artist/**", timeout=8000)
                    logger.info("✅ Navegação confirmada.")
                    self.page.wait_for_selector(S.SEL_BTN_VERDE_ACTION_BAR, state="visible", timeout=6000)
                    return "PERFIL_ABERTO" # <--- MUDANÇA AQUI
                except:
                    logger.warning("⚠️ URL não mudou. Verifique se o play iniciou mesmo assim.")
                    return False

        except Exception as e:
            logger.error(f"Erro no Tab Hunter: {e}")
            return False