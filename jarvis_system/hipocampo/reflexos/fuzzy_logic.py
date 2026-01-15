import logging
import os
from difflib import SequenceMatcher, get_close_matches

logger = logging.getLogger("REFLEXOS_FUZZY")

# Cache para não ler o arquivo toda vez (Performance)
CACHE_ARTISTAS = []

def carregar_memoria_artistas():
    """Lê a biblioteca musical para aprender nomes de artistas."""
    global CACHE_ARTISTAS
    if CACHE_ARTISTAS: return CACHE_ARTISTAS

    # Caminho até a raiz/biblioteca_musical.txt
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.abspath(os.path.join(current_dir, '../../..'))
        path_biblio = os.path.join(root_dir, "biblioteca_musical.txt")

        if os.path.exists(path_biblio):
            with open(path_biblio, 'r', encoding='utf-8') as f:
                for linha in f:
                    # Formato esperado: "Musica - Artista" ou apenas nomes
                    partes = linha.split('-')
                    if len(partes) > 1:
                        artista = partes[1].strip()
                        CACHE_ARTISTAS.append(artista)
            
            # Adiciona manuais importantes caso não estejam na lista
            CACHE_ARTISTAS.extend(["Frei Gilson", "Metallica", "Pink Floyd", "The Weeknd"])
            
            # Remove duplicatas e limpa
            CACHE_ARTISTAS = list(set([a for a in CACHE_ARTISTAS if len(a) > 3]))
            logger.info(f"📚 Memória Fonética: {len(CACHE_ARTISTAS)} artistas carregados.")
        else:
            logger.warning("⚠️ biblioteca_musical.txt não encontrada. Correção contextual limitada.")
    except Exception as e:
        logger.error(f"Erro ao ler biblioteca musical: {e}")

    return CACHE_ARTISTAS

def sugerir_correcao_artista(texto_sujo):
    """
    Se o usuário disse 'tocar X', verifica se X se parece com algum artista conhecido.
    Ex: 'tocar fringe wilson' -> 'tocar Frei Gilson'
    """
    artistas = carregar_memoria_artistas()
    if not artistas: return texto_sujo

    texto_lower = texto_sujo.lower()
    
    # Palavras-gatilho de música
    gatilhos = ["tocar", "reproduzir", "ouve", "ouvir", "bota"]
    tem_gatilho = any(g in texto_lower for g in gatilhos)

    if tem_gatilho:
        # Tenta isolar o que foi dito após o gatilho
        # Ex: "tocar fringe wilson" -> "fringe wilson"
        termo_busca = texto_lower
        for g in gatilhos:
            termo_busca = termo_busca.replace(g, "")
        
        termo_busca = termo_busca.strip()
        
        # Busca o artista mais parecido (Cutoff 0.5 = 50% de semelhança aceitável)
        matches = get_close_matches(termo_busca, artistas, n=1, cutoff=0.5)
        
        if matches:
            artista_correto = matches[0]
            # Se a similaridade for muito alta, substitui
            ratio = SequenceMatcher(None, termo_busca, artista_correto.lower()).ratio()
            
            if ratio > 0.5:
                logger.info(f"🧠 Correção Contextual: '{termo_busca}' -> '{artista_correto}' ({ratio:.2f})")
                # Reconstrói a frase preservando o comando 'tocar' se existir
                if "tocar" in texto_lower:
                    return f"tocar {artista_correto}"
                return artista_correto

    return texto_sujo

def aplicar_fuzzy(texto, mapa_correcoes, threshold=0.75):
    """
    Fluxo principal de correção.
    """
    texto_final = texto

    # 1. Tenta correção inteligente de artista (Baseada em Memória)
    texto_final = sugerir_correcao_artista(texto_final)

    # 2. Tenta correção manual (speech_config.json)
    palavras = texto_final.split()
    if not palavras: return texto_final
    
    for errado, correto in mapa_correcoes.items():
        n_words = len(errado.split())
        if n_words > len(palavras): continue
        
        for i in range(len(palavras) - n_words + 1):
            trecho_lista = palavras[i : i + n_words]
            trecho_str = " ".join(trecho_lista)
            
            similaridade = SequenceMatcher(None, trecho_str.lower(), errado.lower()).ratio()
            
            if similaridade >= threshold:
                logger.info(f"✨ Correção Fuzzy Manual: '{trecho_str}' -> '{correto}'")
                texto_final = texto_final.replace(trecho_str, correto, 1)
                palavras = texto_final.split() 
                break 
                
    return texto_final