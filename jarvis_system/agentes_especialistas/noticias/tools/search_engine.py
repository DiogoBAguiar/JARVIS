import logging
import feedparser
import json
import os
from duckduckgo_search import DDGS

logger = logging.getLogger("NEWS_ENGINE")

class NewsEngine:
    def __init__(self):
        self.ddgs = DDGS()
        self.rss_sources = self._carregar_fontes()

    def _carregar_fontes(self):
        """Carrega as fontes RSS do arquivo JSON externo."""
        try:
            # Obtém o caminho absoluto do diretório onde este arquivo .py está
            base_path = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(base_path, "sources.json")
            
            if not os.path.exists(json_path):
                logger.warning(f"⚠️ Arquivo sources.json não encontrado em: {json_path}")
                return {} # Retorna vazio ou um fallback básico se preferir

            with open(json_path, 'r', encoding='utf-8') as f:
                sources = json.load(f)
                logger.info(f"✅ Mapa de fontes carregado: {len(sources)} categorias.")
                return sources
        except Exception as e:
            logger.error(f"❌ Erro ao carregar sources.json: {e}")
            return {}

    def get_briefing(self, categoria="geral", limit=6):
        """
        Modo Passivo Multi-Fonte:
        Percorre a lista de fontes da categoria, pega um pouco de cada e mistura.
        """
        # Garante que urls seja sempre uma lista, mesmo se não achar a categoria
        urls = self.rss_sources.get(categoria, self.rss_sources.get("geral", []))
        
        # Se urls for string (legado) ou lista vazia, trata
        if isinstance(urls, str): urls = [urls]
        if not urls:
            logger.warning(f"⚠️ Nenhuma fonte definida para categoria: {categoria}")
            return []
        
        logger.info(f"📡 Iniciando Varredura Multi-Fonte para: {categoria} ({len(urls)} fontes)")
        
        todas_noticias = []
        limit_per_source = 2 
        
        for url in urls:
            try:
                feed = feedparser.parse(url)
                if not feed.entries:
                    continue 

                fonte_nome = feed.feed.get("title", "Fonte Externa")
                fonte_limpa = fonte_nome.replace("G1 > ", "").replace(" - Últimas notícias", "")

                for entry in feed.entries[:limit_per_source]:
                    todas_noticias.append({
                        "titulo": entry.title,
                        "link": entry.link,
                        "publicado_em": entry.get("published", "Recente"),
                        "fonte": fonte_limpa,
                        "image": self._extrair_imagem_rss(entry)
                    })
            except Exception as e:
                logger.warning(f"⚠️ Falha ao ler fonte {url}: {e}")
                continue

        return todas_noticias[:limit]

    def _extrair_imagem_rss(self, entry):
        """Tenta encontrar imagem dentro da entrada RSS."""
        try:
            if 'media_content' in entry:
                return entry.media_content[0]['url']
            if 'media_thumbnail' in entry:
                return entry.media_thumbnail[0]['url']
            if 'links' in entry:
                for link in entry.links:
                    if 'image' in link.type:
                        return link.href
        except:
            pass
        return None

    def search_topic(self, query, limit=3):
        """Modo Ativo: Pesquisa Web"""
        logger.info(f"🌍 Pesquisando na Web: '{query}'...")
        try:
            results = self.ddgs.news(keywords=query, region="br-pt", safesearch="off", max_results=limit)
            clean_results = []
            for r in results:
                clean_results.append({
                    "titulo": r.get('title'),
                    "resumo": r.get('body'), 
                    "link": r.get('url'),
                    "fonte": r.get('source'),
                    "data": r.get('date'),
                    "image": r.get('image')
                })
            return clean_results
        except Exception as e:
            logger.error(f"Erro no DuckDuckGo: {e}")
            return []