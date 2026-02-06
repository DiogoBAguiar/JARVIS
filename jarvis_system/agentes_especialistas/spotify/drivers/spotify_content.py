import time
import logging

try:
    from .spotify_selectors import SpotifySelectors as S
except ImportError:
    from spotify_selectors import SpotifySelectors as S

logger = logging.getLogger("SPOTIFY_CONTENT")

class SpotifyContentMixin:
    """Mixin responsável por interagir com filtros, perfis e listas."""

    # ... (MÉTODOS PADRÃO MANTIDOS) ...
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
        return self.entrar_no_perfil_artista_rigoroso(nome_alvo)

    # =========================================================================
    # MÉTODOS RIGOROSOS (TAB HUNTER - LÓGICA DE PLAY DIRETO)
    # =========================================================================

    def aplicar_filtro_rigoroso(self, nome_filtro: str) -> bool:
        # (Mantido igual, funciona bem)
        try:
            chip = self.page.locator(f'{S.SEL_FILTRO_CHIP}:has-text("{nome_filtro}")').first
            if chip.is_visible():
                if chip.get_attribute("aria-checked") == "true":
                    logger.info(f"✅ Filtro '{nome_filtro}' já estava ativo.")
                    return True
                
                # JS Click para garantir
                chip.evaluate("e => e.click()")
                time.sleep(2.0)
                
                if chip.get_attribute("aria-checked") == "true":
                    logger.info(f"✅ Filtro '{nome_filtro}' confirmado ativo.")
                    return True
        except: pass
        return False

    def entrar_no_perfil_artista_rigoroso(self, nome_alvo: str) -> bool:
        """
        Estratégia TAB HUNTER (Com Detecção de Play):
        1. Caça o elemento com TAB.
        2. Se o texto for 'Tocar Matuê', dá Enter e SUCESSO IMEDIATO (Play Direto).
        3. Se o texto for 'Matuê' (Link), dá Enter e valida mudança de página.
        """
        logger.info(f"🧐 [Auditoria] Iniciando TAB HUNTER para: '{nome_alvo}'...")
        
        try:
            # 1. Reset de Foco (Clica no fundo da main area para garantir inicio limpo)
            try:
                self.page.locator(S.SEL_AREA_PRINCIPAL).click(position={"x": 10, "y": 10}, force=True)
            except:
                self.page.mouse.click(0, 0) # Fallback
                
            time.sleep(0.5)

            # 2. Loop de TAB (Caça ao Tesouro)
            max_tabs = 50 
            encontrou = False
            play_direto = False # Flag para saber se foi play direto
            
            for i in range(max_tabs):
                self.page.keyboard.press("Tab")
                
                # Pega o texto do elemento focado
                texto_focado = self.page.evaluate("document.activeElement.innerText || document.activeElement.getAttribute('aria-label') || ''")
                texto_focado_lower = texto_focado.lower()
                alvo_lower = nome_alvo.lower()

                # LOG DE DEBUG (Útil para ver onde o foco está passando)
                # if i % 5 == 0: logger.info(f"   -> Tab {i}: '{texto_focado[:30]}...'")

                # CASO 1: Foco no Botão de Play ("Tocar Matuê")
                if ("tocar" in texto_focado_lower or "play" in texto_focado_lower) and alvo_lower in texto_focado_lower:
                    logger.info(f"▶️ ALVO 'PLAY' LOCALIZADO no Tab {i+1}! Texto: '{texto_focado}'")
                    play_direto = True
                    encontrou = True
                    break
                
                # CASO 2: Foco no Link do Artista ("Matuê")
                elif alvo_lower == texto_focado_lower or alvo_lower in texto_focado_lower:
                    # Evita falsos positivos curtos se o nome for comum, mas no modo rigoroso aceitamos
                    logger.info(f"👤 ALVO 'PERFIL' LOCALIZADO no Tab {i+1}! Texto: '{texto_focado}'")
                    encontrou = True
                    break
                
                time.sleep(0.05) # Acelerei um pouco

            if not encontrou:
                logger.error(f"❌ Não encontrei '{nome_alvo}' após {max_tabs} Tabs.")
                return False

            # 3. Disparo (ENTER)
            logger.info("⚡ Pressionando ENTER no alvo focado...")
            self.page.keyboard.press("Enter")
            time.sleep(2.0) # Espera a ação acontecer

            # --- DECISÃO DE SUCESSO ---
            
            if play_direto:
                # SE DEU PLAY DIRETO: NÃO ESPERA MUDAR DE PÁGINA!
                logger.info("🎉 Play acionado diretamente na lista! Pulando verificação de perfil.")
                return True
            else:
                # SE CLICOU NO PERFIL: TEM QUE MUDAR DE PÁGINA
                logger.info("⏳ Aguardando navegação para perfil...")
                try:
                    self.page.wait_for_url("**/artist/**", timeout=8000)
                    logger.info("✅ Navegação confirmada.")
                    # Espera o botão verde carregar para garantir que o DOM está pronto
                    self.page.wait_for_selector(S.SEL_BTN_VERDE_ACTION_BAR, state="visible", timeout=6000)
                    return True
                except:
                    # Se não navegou, pode ser que tenha dado play sem querer ou falhou.
                    # Vamos assumir erro se não navegou no modo perfil.
                    logger.warning("⚠️ URL não mudou. Verifique se o play iniciou mesmo assim.")
                    return False

        except Exception as e:
            logger.error(f"Erro no Tab Hunter: {e}")
            return False