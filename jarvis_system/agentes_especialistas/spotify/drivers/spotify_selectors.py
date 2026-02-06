class SpotifySelectors:
    """
    MAPA DE SELETORES DO SPOTIFY WEB (VERSÃO 2026 - FINAL)
    Atualizado com dados reais do HTML da Grid de Artistas.
    """

    # =========================================================================
    # 1. CABEÇALHO E NAVEGAÇÃO
    # =========================================================================
    SEL_LOGO = 'a[href="/"][class*="logo"], a[aria-label="Spotify"]'
    SEL_HOME = 'button[data-testid="home-button"]'
    SEL_BUSCA_ABRIR = 'button[data-testid="search-icon"]'
    SEL_BUSCA_INPUT = 'input[data-testid="search-input"]'
    SEL_LIMPAR_BUSCA = 'button[data-testid="clear-button"]'
    SEL_NAVEGAR = 'button[data-testid="browse-button"]'
    SEL_NOTIFICACOES = 'button[data-testid="whats-new-feed-button"]'
    SEL_AMIGOS = 'button[data-testid="friend-activity-button"]'
    SEL_PERFIL = 'button[data-testid="user-widget-link"]'

    # =========================================================================
    # 2. BARRA LATERAL
    # =========================================================================
    SEL_BTN_BIBLIOTECA = 'button[aria-label="Abrir Sua Biblioteca"], button[aria-label="Fechar Sua Biblioteca"]'
    SEL_BTN_CRIAR = 'button[aria-label="Criar"]'
    SEL_MENU_CRIAR_PLAYLIST = 'button:has(#listrow-title-global-create-playlist)'
    SEL_MENU_CRIAR_MATCH = 'button:has(#listrow-title-global-create-blend)'
    SEL_MENU_CRIAR_PASTA = 'button:has(#listrow-title-global-create-folder)'

    # =========================================================================
    # 3. LISTAS E PLAYLISTS
    # =========================================================================
    SEL_MUSICAS_CURTIDAS_ROW = 'div[role="gridcell"]:has-text("Músicas Curtidas")'
    SEL_BTN_PLAY_CURTIDAS = 'button[aria-label="Tocar Músicas Curtidas"]'
    SEL_PLAYLIST_ROW = 'div[role="row"]'
    SEL_PLAYLIST_POR_NOME = 'div[role="row"]:has-text("{}")'

    # =========================================================================
    # 4. ÁREA PRINCIPAL E FILTROS
    # =========================================================================
    SEL_AREA_PRINCIPAL = 'main' # Onde vive o conteúdo real
    
    # Filtros (Chips)
    SEL_FILTRO_CHIP = 'button[role="checkbox"]' 
    # Seleciona especificamente o chip que está ativo (verde/branco)
    SEL_FILTRO_ATIVO = 'button[role="checkbox"][aria-checked="true"]'

    # =========================================================================
    # 5. RESULTADOS (TOP RESULT vs GRID) [ATUALIZADO]
    # =========================================================================
    # Visualização "Tudo" (Geralmente tem um destaque grande)
    SEL_TOP_RESULT_CARD = 'div[data-testid="top-result-card"]'
    
    # Visualização "Filtro Ativo" (Grid de Cards: search-category-card-0, etc)
    # Esse é o seletor genérico para qualquer card da grade
    SEL_GRID_CARD = 'div[data-testid^="search-category-card-"]'
    
    # Seletor Poderoso: Encontra o card da grid que tem o Título do Artista
    # Procura um card de grid que contenha um link com title="Matuê" ou texto "Matuê"
    SEL_CARD_GRID_POR_NOME = 'div[data-testid^="search-category-card-"]:has(a[title="{}"]), div[data-testid^="search-category-card-"]:has-text("{}")'

    # Links dentro dos cards (para validação)
    SEL_CARD_ARTISTA = 'a[href*="/artist/"]'
    SEL_CARD_PLAYLIST = 'div[aria-labelledby*="spotify:playlist:"]'
    SEL_CARD_ALBUM = 'div[aria-labelledby*="spotify:album:"]'
    SEL_TRACK_LINK = 'a[href*="/track/"]'
    SEL_TRACK_POR_NOME = 'a[href*="/track/"]:has-text("{}")'

    # =========================================================================
    # 6. BOTÕES DE PLAY
    # =========================================================================
    SEL_PLAY_BUTTON_GENERIC = 'button[data-testid="play-button"]'
    SEL_BTN_VERDE_ACTION_BAR = 'div[data-testid="action-bar-row"] button[data-testid="play-button"]'
    
    # Play Específico dentro de um Card da Grid (Mais preciso)
    SEL_PLAY_ON_GRID_CARD = 'div[data-testid^="search-category-card-"] button[data-testid="play-button"]'

    # =========================================================================
    # 7. RODAPÉ, CONTROLES E ADS
    # =========================================================================
    SEL_NOW_TRACK = 'a[data-testid="context-item-link"]'
    SEL_NOW_ARTIST = 'a[data-testid="context-item-info-artist"]'
    SEL_LIKE = 'button[aria-label="Adicionar a Músicas Curtidas"]'
    SEL_UNLIKE = 'button[aria-label="Remover de Músicas Curtidas"]'
    SEL_SHUFFLE = 'button[data-testid="control-button-shuffle"]'
    SEL_PREV = 'button[data-testid="control-button-skip-back"]'
    SEL_PLAY_PAUSE = 'button[data-testid="control-button-playpause"]'
    SEL_NEXT = 'button[data-testid="control-button-skip-forward"]'
    SEL_REPEAT = 'button[data-testid="control-button-repeat"]'
    SEL_LYRICS = 'button[data-testid="lyrics-button"]'
    SEL_QUEUE = 'button[data-testid="control-button-queue"]'
    SEL_MUTE = 'button[data-testid="volume-bar-toggle-mute-button"]'
    SEL_PIP = 'button[data-testid="pip-toggle-button"]'
    SEL_FULLSCREEN = 'button[data-testid="fullscreen-mode-button"]'
    SEL_AD_LINK = 'a[data-testid="context-item-info-ad-title"]'
    SEL_AD_IFRAME = 'iframe[title*="Advertisement"], iframe[title*="Anúncio"]'

    # =========================================================================
    # 8. DISPOSITIVOS E TÍTULOS
    # =========================================================================
    SEL_CONNECT_DEVICE = 'button[data-testid="control-button-connect-device"], button[aria-label="Conectar a um dispositivo"]'
    SEL_DEVICE_ITEM_TEXT = 'button:has-text("{}"), div[role="button"]:has-text("{}"), p:has-text("{}")'
    SEL_TITULO_PAGINA = 'h1[data-testid="entityTitle"], h1'