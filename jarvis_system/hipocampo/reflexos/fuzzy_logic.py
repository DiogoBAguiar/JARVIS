import logging
from difflib import SequenceMatcher

logger = logging.getLogger("REFLEXOS_FUZZY")

def aplicar_fuzzy(texto, mapa_correcoes, threshold=0.75):
    """
    Substitui trechos do texto baseados em similaridade.
    """
    texto_final = texto
    palavras = texto.split()
    if not palavras: return texto
    
    for errado, correto in mapa_correcoes.items():
        n_words = len(errado.split())
        
        # Otimização: Se o erro é maior que a frase, pula
        if n_words > len(palavras): continue
        
        # Janela deslizante
        for i in range(len(palavras) - n_words + 1):
            trecho_lista = palavras[i : i + n_words]
            trecho_str = " ".join(trecho_lista)
            
            similaridade = SequenceMatcher(None, trecho_str.lower(), errado.lower()).ratio()
            
            if similaridade >= threshold:
                logger.info(f"✨ Correção Fuzzy: '{trecho_str}' ({similaridade:.2f}) -> '{correto}'")
                
                # Substitui apenas a primeira ocorrência encontrada para evitar loop infinito
                texto_final = texto_final.replace(trecho_str, correto, 1)
                
                # Recalcula tokens e reinicia para garantir consistência
                palavras = texto_final.split() 
                break 
                
    return texto_final