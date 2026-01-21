"""
Configurações estáticas do Agente de Notícias.
"""

AGENT_NAME = "Agente Jornalista (Daily Planet)"
VERSION = "1.1.0"

# GATILHOS EXPANDIDOS
TRIGGERS = [
    # Intenções Genéricas
    "noticia", "notícia", "noticias", "notícias",
    "manchete", "manchetes",
    "novidade", "novidades",
    "resumo", "briefing",
    "aconteceu", "acontecendo",
    "lançou", "lançamento", # Para "O que a OpenAI lançou?"
    
    # Tópicos Específicos (Garantem que o agente acorde)
    "futebol", "jogo", "esporte",
    "tech", "tecnologia", "ia", "inteligencia artificial", "openai", "google", "apple",
    "crypto", "bitcoin", "btc", "ethereum",
    "economia", "dolar", "bolsa", "preço"
]

DEFAULT_MAX_RESULTS = 5
TIMEOUT_SEARCH = 10 

SOURCES_METADATA = {
    "rss": "Alta Velocidade / Confiabilidade",
    "search": "Alta Abrangência / Web Aberta"
}