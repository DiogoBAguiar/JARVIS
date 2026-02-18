import json
import os
import logging
import feedparser
from datetime import datetime
from duckduckgo_search import DDGS

logger = logging.getLogger("NEWS_ENGINE")

class NewsEngine:
    def __init__(self):
        # Define o caminho do arquivo sources.json
        self.sources_file = os.path.join(os.path.dirname(__file__), "sources.json")
        self.config = self._load_sources()
        self.ddgs = DDGS()

    def _load_sources(self):
        """Carrega e valida o arquivo sources.json."""
        try:
            if not os.path.exists(self.sources_file):
                logger.warning(f"⚠️ Arquivo sources.json não encontrado em: {self.sources_file}")
                return {}
            
            with open(self.sources_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info(f"✅ Configurações de fontes carregadas (v{config.get('version', '1.0')})")
                return config
        except Exception as e:
            logger.error(f"❌ Erro ao ler sources.json: {e}")
            return {}

    def get_sources_by_category(self, category_name):
        """
        Navega na estrutura hierárquica do JSON para encontrar as fontes.
        Ex: 'futebol' -> Retorna lista de fontes do GE, Lance, UOL.
        """
        if not self.config or "categories" not in self.config:
            return []

        # Normaliza a busca (converte para minúsculo)
        cat_data = self.config["categories"].get(category_name.lower())
        
        # Se não achar a categoria específica, tenta 'geral' como fallback
        if not cat_data and category_name != 'geral':
            logger.warning(f"⚠️ Categoria '{category_name}' não encontrada. Usando 'geral'.")
            cat_data = self.config["categories"].get("geral")

        if cat_data:
            return cat_data.get("sources", [])
        
        return []

    def _extract_image(self, entry):
        """
        Tenta encontrar a melhor imagem possível no RSS.
        Crucial para o visual do Jornal PDF.
        """
        try:
            # 1. Media Content (Padrão Yahoo/G1)
            if "media_content" in entry:
                media = entry.media_content[0]
                if 'url' in media: return media['url']
            
            # 2. Media Thumbnail
            if "media_thumbnail" in entry:
                return entry.media_thumbnail[0]['url']
            
            # 3. Links com type image
            if "links" in entry:
                for link in entry.links:
                    if "image" in str(link.type):
                        return link.href
            
            # 4. Enclosures (Podcasts/Imagens antigas)
            if "enclosures" in entry:
                for enc in entry.enclosures:
                    if "image" in str(enc.type):
                        return enc.href
                        
        except Exception:
            pass
        return None

    def search_topic(self, query, limit=5):
        """
        Modo Ativo: Pesquisa Web (DuckDuckGo).
        Usado quando o RSS não é suficiente ou para assuntos específicos.
        """
        logger.info(f"🌍 Pesquisando na Web: '{query}'...")
        results = []
        try:
            # max_results controla quantos links o DDG retorna
            ddg_news = self.ddgs.news(keywords=query, region="br-pt", safesearch="off", max_results=limit)
            
            if ddg_news:
                for item in ddg_news:
                    results.append({
                        "titulo": item.get('title'),
                        "link": item.get('url'),
                        "fonte": item.get('source', 'Web Search'),
                        "publicado_em": item.get('date', datetime.now().isoformat()),
                        "image": item.get('image', None),
                        "resumo": item.get('body', ''),
                        "reliability": 0.5 # Web Search tem confiabilidade padrão média
                    })
            
        except Exception as e:
            logger.error(f"⚠️ Erro na Busca Web (DuckDuckGo): {e}")
        
        return results

    def get_briefing(self, categoria="geral", limit=3):
        """
        Busca notícias via RSS das fontes configuradas no novo JSON.
        """
        sources = self.get_sources_by_category(categoria)
        if not sources:
            logger.warning(f"⚠️ Nenhuma fonte configurada para: {categoria}")
            return []

        all_news = []
        
        # Pega a política de atualização do JSON ou usa padrão
        policy_limit = self.config.get("update_policy", {}).get("max_articles_per_source", 5)
        # Se o limit passado for menor que a política, usa a política para ter variedade
        limit_per_source = policy_limit

        logger.info(f"📡 Varrendo {len(sources)} fontes de '{categoria}'...")

        for source in sources:
            # Pula fontes inativas no JSON
            if not source.get("active", True): 
                continue

            try:
                # Parse do RSS
                feed = feedparser.parse(source["url"])
                
                if not feed.entries:
                    continue

                # Pega os artigos
                count = 0
                for entry in feed.entries:
                    if count >= limit_per_source: break
                    
                    news_item = {
                        "titulo": entry.title,
                        "link": entry.link,
                        # Usa o nome bonito do JSON (ex: "G1 Tecnologia") em vez do título do feed
                        "fonte": source["name"],
                        "publicado_em": entry.get("published", datetime.now().isoformat()),
                        "image": self._extract_image(entry),
                        "resumo": entry.get("summary", "")[:300] + "...", # Limita resumo para não estourar prompt
                        "reliability": source.get("reliability", 0.7) # Passa a confiabilidade do JSON
                    }
                    all_news.append(news_item)
                    count += 1
                    
            except Exception as e:
                logger.debug(f"Falha ao ler {source.get('name')}: {e}")

        # Retorna todas as notícias encontradas (o cérebro filtra depois se precisar)
        return all_news