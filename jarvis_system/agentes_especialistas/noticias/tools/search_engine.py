import logging
import feedparser
from duckduckgo_search import DDGS
from datetime import datetime

logger = logging.getLogger("NEWS_ENGINE")

class NewsEngine:
    def __init__(self):
        self.ddgs = DDGS()
        
        # 🗺️ MAPA DE FONTES (Curadoria Otimizada)
        self.rss_sources = {
            # 🏠 Local & Brasil
            "geral": "https://g1.globo.com/rss/g1/",
            "paraiba": "https://g1.globo.com/rss/g1/pb/paraiba/",
            
            # ⚽ Esportes (Futebol)
            "esporte": "https://ge.globo.com/rss/ge/",
            "futebol": "https://www.espn.com.br/espn/rss/news",
            
            # 💻 Tech & Crypto
            "tecnologia": "https://g1.globo.com/rss/g1/tecnologia/",
            # FIX: Cointelegraph estava bloqueando requisições. Usando UOL (mais estável).
            "crypto": "https://portaldobitcoin.uol.com.br/feed/",
            
            # 💹 Economia
            "economia": "https://g1.globo.com/rss/g1/economia/",
            "dolar": "https://br.investing.com/rss/news_1.rss",
            "cnn_business": "https://www.cnnbrasil.com.br/economia/feed/"
        }

    def get_briefing(self, categoria="geral", limit=5):
        """
        Modo Passivo: Pega as últimas manchetes de uma fonte confiável.
        Ideal para: "Jarvis, resumo do dia" ou "Notícias do Esporte".
        """
        url = self.rss_sources.get(categoria, self.rss_sources["geral"])
        logger.info(f"📡 Lendo RSS: {categoria} ({url})...")
        
        try:
            feed = feedparser.parse(url)
            
            # FIX: Verifica se o RSS retornou algo antes de tentar ler
            if not feed.entries:
                logger.warning(f"⚠️ Fonte RSS vazia ou bloqueada: {url}")
                return []

            noticias = []
            for entry in feed.entries[:limit]:
                noticias.append({
                    "titulo": entry.title,
                    "link": entry.link,
                    "publicado_em": entry.get("published", "Hoje"),
                    "fonte": feed.feed.get("title", "RSS")
                })
            return noticias
        except Exception as e:
            logger.error(f"Erro ao ler RSS: {e}")
            return []

    def search_topic(self, query, limit=3):
        """
        Modo Ativo: Pesquisa profunda sobre qualquer assunto na Web.
        Ideal para: "Jarvis, o que aconteceu com a Nvidia?"
        """
        logger.info(f"🌍 Pesquisando na Web: '{query}'...")
        try:
            # region="br-pt" foca em fontes brasileiras
            results = self.ddgs.news(keywords=query, region="br-pt", safesearch="off", max_results=limit)
            
            clean_results = []
            for r in results:
                clean_results.append({
                    "titulo": r.get('title'),
                    "resumo": r.get('body'), # O DDG já traz um mini-resumo!
                    "link": r.get('url'),
                    "fonte": r.get('source'),
                    "data": r.get('date')
                })
            return clean_results
        except Exception as e:
            logger.error(f"Erro no DuckDuckGo: {e}")
            return []