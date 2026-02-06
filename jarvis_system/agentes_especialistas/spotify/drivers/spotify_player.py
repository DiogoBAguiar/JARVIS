import time
import logging

# --- CORREÇÃO DE IMPORTAÇÃO ---
try:
    from .spotify_selectors import SpotifySelectors as S
except ImportError:
    from spotify_selectors import SpotifySelectors as S

logger = logging.getLogger("SPOTIFY_PLAYER")

class SpotifyPlayerMixin:
    """Mixin responsável por Play, Pause, Dispositivos e Leitura (Com Validação Rigorosa)."""

    # ... (MANTENHA TODO O RESTO DO CÓDIGO IGUAL AO QUE JÁ TINHA) ...
    # Só a parte de cima dos imports que mudou.
    
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
            time.sleep(3)
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
                    logger.warning(f"❌ [Erro] Tocando '{track}' de '{artist}', mas pedi '{termo_esperado}'.")
                    return False 
            else:
                logger.warning("⚠️ Rodapé vazio ou carregando... tentando novamente.")
        logger.error("❌ Falha na validação após todas as tentativas.")
        return False

    def conectar_no_jarvas(self, device_name="JARVAS") -> bool:
        logger.info(f"📡 Buscando dispositivo '{device_name}'...")
        try:
            btn_menu = self.page.locator(S.SEL_CONNECT_DEVICE)
            if btn_menu.count() > 0:
                 btn_menu.click()
                 time.sleep(1.5) 
            selector = S.SEL_DEVICE_ITEM_TEXT.format(device_name, device_name, device_name)
            jarvas_btn = self.page.locator(selector).first
            if jarvas_btn.is_visible():
                jarvas_btn.click()
                logger.info(f"✅ Conectado ao {device_name}!")
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
            btn = self.page.locator(S.SEL_BTN_PLAY_CURTIDAS).first
            if btn.is_visible():
                btn.click()
                return True
            row = self.page.locator(S.SEL_MUSICAS_CURTIDAS_ROW).first
            if row.is_visible():
                row.click()
                time.sleep(1.5)
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