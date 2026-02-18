"""
Configurações estáticas do Agente de Notícias.
"""

AGENT_NAME = "Agente Jornalista (Daily Planet)"
VERSION = "3.0.0"

# GATILHOS EXPANDIDOS (Vocabulário do Porteiro)
TRIGGERS = [
    # --- Intenções Genéricas ---
    "noticia", "notícia", "noticias", "notícias",
    "manchete", "manchetes", "novidade", "novidades",
    "resumo", "briefing", "aconteceu", "acontecendo",
    "informacao", "informação", "reportagem", "jornal",
    "fale sobre", "me diga sobre", "saber sobre",
    "quem ganhou", "quem venceu", "resultado", "placar",
    
    # --- Tópicos: Esportes & E-Sports ---
    "futebol", "jogo", "partida", "campeonato", "copa", "brasileirao",
    "esporte", "esports", "cs", "valorant", "lol", "league of legends", 
    "fallen", "furia", "loud", "pain", "cblol",
    
    # --- Tópicos: Tech & Nerd ---
    "tech", "tecnologia", "celular", "iphone", "samsung", "apple", "google", 
    "xiaomi", "lançamento", "lançou",
    "nerd", "geek", "otaku", "anime", "manga", "filme", "serie", "cinema",
    "games", "videogame", "playstation", "xbox", "nintendo", "steam",
    "ia", "inteligencia artificial", "openai", "chatgpt", "gemini",
    
    # --- Tópicos: Economia & Crypto ---
    "economia", "mercado", "bolsa", "dolar", "euro", "selic", "juros",
    "bitcoin", "btc", "ethereum", "crypto", "cripto", "moeda", 
    "investimento", "acao", "acoes", "binance", "preço", "cotacao",
    
    # --- Tópicos: Ciência & Política ---
    "politica", "governo", "leis", "senado", "congresso", "presidente", "stf",
    "ciencia", "cientifica", "espaco", "nasa", "universo", "descoberta",
    "saude", "vacina", "doenca", "virus", "bem-estar",
    
    # --- Inglês (Opcional) ---
    "news", "breaking news", "what happened"
]

DEFAULT_MAX_RESULTS = 5
TIMEOUT_SEARCH = 10 

SOURCES_METADATA = {
    "rss": "Alta Velocidade / Confiabilidade",
    "search": "Alta Abrangência / Web Aberta"
}