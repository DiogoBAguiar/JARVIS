import re
import logging

# Configuração de Log para monitorar a compilação
logger = logging.getLogger("REGEX_COMPILER")

def compilar_padroes(mapa_correcoes):
    """
    Transforma um dicionário de correções {errado: certo} em 
    UMA ÚNICA expressão regular otimizada.
    
    Retorna: Lista contendo uma única tupla [(BigRegex, CallbackFunction)]
    Isso mantém compatibilidade com o loop do core.py, mas executa em 1 passo.
    """
    if not mapa_correcoes:
        return []

    # 1. ORDENAÇÃO CRÍTICA (Do maior para o menor)
    # Motivo: Se temos {"são": "x", "são paulo": "y"}, precisamos checar 
    # "são paulo" primeiro. Se checar "são" antes, quebra a frase composta.
    chaves_ordenadas = sorted(mapa_correcoes.keys(), key=len, reverse=True)

    # 2. ESCAPE (Segurança)
    # Garante que palavras como "C++" ou "Node.js" não quebrem o Regex com caracteres especiais
    chaves_escapadas = [re.escape(k) for k in chaves_ordenadas]

    # 3. CONSSTRUÇÃO DO "MEGAZORD REGEX"
    # Cria algo como: \b(palavra1|palavra2|palavra3...)\b
    # O motor de regex do Python (escrito em C) é extremamente rápido nisso.
    padrao_unificado = r'\b(' + '|'.join(chaves_escapadas) + r')\b'

    try:
        # Compila a expressão regular
        regex_compiled = re.compile(padrao_unificado, re.IGNORECASE)

        # 4. FUNÇÃO DE CALLBACK (Closure)
        # Em vez de passar uma string de substituição fixa, passamos esta função.
        # O re.sub() chama essa função toda vez que encontra um match.
        def callback_substituicao(match):
            # Pega a palavra que foi encontrada no texto original
            palavra_encontrada = match.group(0)
            
            # Converte para minúsculo para buscar no dicionário (chave de lookup)
            chave_lookup = palavra_encontrada.lower()
            
            # Retorna a correção correspondente
            # O .get() garante segurança, retornando a original se algo bizarro acontecer
            return mapa_correcoes.get(chave_lookup, palavra_encontrada)

        logger.info(f"⚡ Regex Otimizado Compilado: {len(chaves_ordenadas)} regras compactadas em 1 varredura.")

        # Retorna uma lista com 1 item. 
        # O core.py vai fazer: regex.sub(callback, texto)
        return [(regex_compiled, callback_substituicao)]

    except re.error as e:
        logger.error(f"❌ Erro fatal ao compilar Regex Mestre: {e}")
        # Em caso de erro catastrófico, retorna lista vazia para não crashar o Jarvis
        return []