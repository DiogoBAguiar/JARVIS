import time
import logging

try:
    from .spotify_selectors import SpotifySelectors as S
except ImportError:
    from spotify_selectors import SpotifySelectors as S

logger = logging.getLogger("SPOTIFY_PLAYER")

class SpotifyPlayerMixin:
    """Mixin responsável por Play, Pause, Dispositivos e Leitura (Com Validação Rigorosa e Espera Dinâmica)."""

    def verificar_se_eh_anuncio(self) -> bool:
        try:
            ad_link = self.page.locator(S.SEL_AD_LINK)
            if ad_link.count() > 0 and ad_link.is_visible(): return True
            frames = self.page.frames
            for frame in frames:
                try:
                    title = frame.title().lower() if frame.title() else ""
                    if "advertisement" in title or "anuncio" in title or "anúncio" in title: return True
                except: continue
            return False
        except: return False

    def validar_reproducao_rigorosa(self, termo_esperado: str, tentativas=3) -> bool:
        logger.info(f"🕵️ [Auditoria] Validando se está tocando: '{termo_esperado}'...")
        for i in range(tentativas):
            # O obter_estado_reproducao já tem um wait_for_selector de 5s, 
            # não precisamos de sleep longo, só uma folga na CPU.
            time.sleep(1)
            
            track, artist = self.obter_estado_reproducao()
            
            if self.verificar_se_eh_anuncio():
                logger.warning(f"⚠️ Detectado ANÚNCIO (Tentativa {i+1}/{tentativas}). Aguardando 10s...")
                time.sleep(10)
                continue
                
            if track:
                termo_lower = termo_esperado.lower()
                match_artista = artist and (termo_lower in artist.lower() or artist.lower() in termo_lower)
                match_track = termo_lower in track.lower()
                if match_artista or match_track:
                    logger.info(f"🎉 [Sucesso] Confirmado tocando: '{track}' - '{artist}'")
                    return True
                else:
                    logger.warning(f"⚠️ [Mismatch] Tocando '{track}', mas pedi '{termo_esperado}'. Aguardando sync...")
                    continue 
            else:
                logger.warning("⚠️ Rodapé vazio ou carregando... tentando novamente.")
                
        logger.error("❌ Falha na validação após todas as tentativas.")
        return False

    def conectar_no_jarvas(self, device_name="JARVAS") -> bool:
        logger.info(f"📡 Buscando dispositivo '{device_name}'...")
        try:
            # Espera inteligente pelo botão de menu de dispositivos (max 2s)
            try:
                self.page.wait_for_selector(S.SEL_CONNECT_DEVICE, timeout=2000)
                btn_menu = self.page.locator(S.SEL_CONNECT_DEVICE).first
                if btn_menu.is_visible():
                    btn_menu.click()
            except Exception:
                logger.warning("Botão de Dispositivos não apareceu a tempo. Tentando sem clicar.")
                 
            selector = S.SEL_DEVICE_ITEM_TEXT.format(device_name, device_name, device_name)
            
            # Espera inteligente até o dispositivo alvo aparecer na lista (max 3s)
            try:
                self.page.wait_for_selector(selector, state="visible", timeout=3000)
                jarvas_btn = self.page.locator(selector).first
            except Exception:
                logger.error(f"❌ O dispositivo '{device_name}' não foi encontrado na lista.")
                self.page.mouse.click(0, 0)
                return False
            
            if jarvas_btn.is_visible():
                jarvas_btn.click()
                logger.info(f"✅ Conectado ao {device_name}!")
                
                # --- RETOMADA FORÇADA DINÂMICA ---
                # Em vez de esperar 2.5s cegamente, verificamos o estado do botão Play.
                try:
                    # Dá 0.5s para o Spotify Web processar o clique
                    time.sleep(0.5)
                    play_pause_btn = self.page.locator('button[data-testid="control-button-playpause"]').first
                    # Tenta ler o atributo aria por até 2 segundos para ver se o estado mudou
                    for _ in range(4):
                        if play_pause_btn.is_visible():
                            aria = play_pause_btn.get_attribute("aria-label") or ""
                            if "Tocar" in aria or "Play" in aria:
                                logger.info("⚠️ A música pausou na transferência. Forçando retomada (Play) no rodapé...")
                                play_pause_btn.click()
                                break
                        time.sleep(0.5)
                except Exception as e:
                    logger.warning(f"Não foi possível checar o status de pausa após transferência: {e}")
                # -----------------------------------------------------

                self.page.mouse.click(0, 0)
                return True
                
            self.page.mouse.click(0, 0)
            return False
        except Exception as e:
            logger.error(f"Erro conexão: {e}")
            self.page.mouse.click(0, 0)
            return False

    def tocar_melhor_resultado(self) -> bool:
        logger.info("▶️ Buscando botão Play Verde...")
        btn_action = self.page.locator(S.SEL_BTN_VERDE_ACTION_BAR).first
        if btn_action.is_visible():
            logger.info("   -> Play Action Bar")
            aria = btn_action.get_attribute("aria-label") or ""
            if "Pausar" in aria:
                logger.info("   ⚠️ Já está tocando.")
                return True
            btn_action.click(force=True)
            return True
            
        btn_top = self.page.locator(f'{S.SEL_TOP_RESULT_CARD} {S.SEL_PLAY_BUTTON_GENERIC}').first
        if btn_top.is_visible():
            logger.info("   -> Play Top Result")
            btn_top.click(force=True)
            return True
            
        btn_generic = self.page.locator(S.SEL_PLAY_BUTTON_GENERIC).first
        if btn_generic.is_visible():
            logger.info("   -> Play Genérico")
            btn_generic.click(force=True)
            return True
            
        return False

    def tocar_musicas_curtidas(self) -> bool:
        try:
            # Espera inteligente pelo botão de Play nas músicas curtidas
            try:
                self.page.wait_for_selector(S.SEL_BTN_PLAY_CURTIDAS, timeout=2000)
                btn = self.page.locator(S.SEL_BTN_PLAY_CURTIDAS).first
                if btn.is_visible():
                    btn.click()
                    return True
            except: pass

            row = self.page.locator(S.SEL_MUSICAS_CURTIDAS_ROW).first
            if row.is_visible():
                row.click()
                # Espera inteligente pelo botão de ação (em vez de sleep 1.5)
                self.page.wait_for_selector(S.SEL_BTN_VERDE_ACTION_BAR, state="visible", timeout=3000)
                self.page.locator(S.SEL_BTN_VERDE_ACTION_BAR).click(force=True)
                return True
        except: pass
        return False

    def obter_estado_reproducao(self):
        try:
            self.page.wait_for_selector(S.SEL_NOW_TRACK, timeout=5000)
            track = self.page.locator(S.SEL_NOW_TRACK).first.inner_text()
            artist = self.page.locator(S.SEL_NOW_ARTIST).first.inner_text()
            logger.info(f"🎵 Rodapé diz: '{track}' - '{artist}'")
            return track, artist
        except:
            return None, None