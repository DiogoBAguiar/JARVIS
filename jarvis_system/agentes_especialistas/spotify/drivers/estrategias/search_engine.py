import logging
import time

logger = logging.getLogger("SPOTIFY_SEARCH_STRATEGY")

class SearchEngine:
    """
    CÉREBRO DE BUSCA v2.0
    Responsável por interpretar a intenção do usuário e manipular
    os filtros da interface do Spotify para garantir o resultado exato.
    """

    # Constantes de Texto da UI do Spotify (PT-BR)
    # Devem bater com o texto visível nos botões de filtro (Chips)
    UI_FILTER_PLAYLIST = "Playlists"
    UI_FILTER_ARTIST   = "Artistas"
    UI_FILTER_ALBUM    = "Álbuns"
    UI_FILTER_MUSIC    = "Músicas"
    UI_FILTER_PODCAST  = "Podcasts e programas"

    def __init__(self, page_model):
        self.page = page_model

    def _detectar_intencao_avancada(self, termo: str, tipo_conteudo: str) -> str:
        """
        Cruza o 'tipo_conteudo' (vindo do LLM) com palavras-chave no 'termo'
        para determinar o filtro definitivo.
        Retorna: A constante UI_FILTER_... correspondente ou None.
        """
        texto_analise = f"{termo} {tipo_conteudo}".lower()

        # 1. Mapeamento de Sinônimos para Intenção
        keywords = {
            self.UI_FILTER_PLAYLIST: ["playlist", "lista", "sequencia", "mix", "radio"],
            self.UI_FILTER_ARTIST:   ["artista", "banda", "cantor", "cantora", "grupo", "dupla", "trio"],
            self.UI_FILTER_ALBUM:    ["album", "álbum", "disco", "cd", "lp", "ep"],
            self.UI_FILTER_PODCAST:  ["podcast", "programa", "episodio", "episódio"],
            self.UI_FILTER_MUSIC:    ["musica", "música", "faixa", "som", "track"]
        }

        # 2. Verificação de Prioridade
        for filtro_ui, sinonimos in keywords.items():
            if any(s in texto_analise for s in sinonimos):
                return filtro_ui
        
        return None

    def executar_estrategia(self, termo: str, tipo_conteudo: str) -> bool:
        """
        Executa a lógica de refinamento de busca.
        """
        logger.info(f"🧠 [Strategy] Analisando contexto: Termo='{termo}' | Tipo='{tipo_conteudo}'")

        # 1. Detectar qual botão apertar
        filtro_alvo = self._detectar_intencao_avancada(termo, tipo_conteudo)

        if not filtro_alvo:
            logger.info("🎯 [Strategy] Nenhuma estratégia específica necessária. Usando 'Melhor Resultado'.")
            return True # Retorna True pois não falhou, apenas decidiu não filtrar

        # 2. Executar o Filtro
        logger.info(f"🎯 [Strategy] Alvo identificado: {filtro_alvo.upper()}")
        
        # Caso Especial: Músicas
        # Às vezes filtrar por "Músicas" remove o destaque do topo. 
        # Só aplicamos se for explicitamente pedido.
        if filtro_alvo == self.UI_FILTER_MUSIC:
            if "musica" not in tipo_conteudo.lower():
                logger.info("   -> Ignorando filtro 'Músicas' para manter o Top Result.")
                return True

        # 3. Aplicação no Page Model
        sucesso = self.page.aplicar_filtro(filtro_alvo)
        
        if sucesso:
            # Pausa tática para o DOM do Spotify recriar a lista de resultados
            # Isso evita o "Stale Element Reference Exception"
            time.sleep(1.5) 
            return True
        else:
            logger.warning(f"⚠️ [Strategy] Falha ao clicar no filtro '{filtro_alvo}'. Tentando sem filtro.")
            return False