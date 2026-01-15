import re

def compilar_padroes(mapa_correcoes):
    """
    Retorna lista de tuplas (Pattern, Replacement).
    """
    patterns = []
    for wrong, correct in mapa_correcoes.items():
        # \b garante que só pega palavra inteira
        regex = re.compile(rf'\b{re.escape(wrong)}\b', re.IGNORECASE)
        patterns.append((regex, correct))
    return patterns