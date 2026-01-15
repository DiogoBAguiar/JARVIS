from collections import Counter

# Regras de Negócio Hardcoded
LISTA_BRANCA = [
    "spotify", "brave", "chrome", "jarvis", "tocar", 
    "abrir", "fechar", "volume", "pare", "continuar",
    "music", "música", "youtube", "whatsapp", "pesquisar",
    "clima", "horas", "data", "status"
]

class LogAnalyzer:
    def identificar_ruidos(self, historico_eventos, ruidos_conhecidos=None):
        """
        Recebe lista de eventos [{'frase': 'x', 'status': 'falha'}]
        Retorna lista de strings para bloquear.
        """
        if ruidos_conhecidos is None: ruidos_conhecidos = []
        
        contagem_ruido = Counter()
        contagem_sucesso = Counter()

        # 1. Agregação
        for item in historico_eventos:
            frase = item['frase']
            if item['status'] == "falha":
                # Filtro de Tamanho: Ignora frases muito longas (provavelmente ditado real)
                # ou muito curtas que não sejam comandos
                if len(frase) < 60: 
                    contagem_ruido[frase] += 1
            else:
                contagem_sucesso[frase] += 1

        novos_ruidos = []

        # 2. Aplicação de Regras
        for frase, qtd_falhas in contagem_ruido.items():
            
            # Regra A: Falhou pelo menos 2 vezes
            if qtd_falhas < 2: continue
            
            # Regra B: Nunca teve sucesso (Zero tolerância)
            if contagem_sucesso[frase] > 0: continue
            
            # Regra C: Já conhecemos?
            if frase in ruidos_conhecidos: continue

            # Regra D: É Sagrado? (Lista Branca)
            if self._eh_protegido(frase): continue
            
            novos_ruidos.append(frase)
            
        return novos_ruidos

    def _eh_protegido(self, frase):
        for palavra_sagrada in LISTA_BRANCA:
            if palavra_sagrada in frase:
                return True
        return False