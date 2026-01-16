import logging
import re
from difflib import SequenceMatcher, get_close_matches

# --- CONFIGURAÇÃO DE LOG ---
logger = logging.getLogger("REFLEXOS_FUZZY")

# --- INTEGRAÇÃO COM MEMÓRIA (DB) ---
try:
    from jarvis_system.hipocampo.memoria import memoria
except ImportError:
    memoria = None

CACHE_ARTISTAS = []

def carregar_memoria_artistas(force_refresh=False):
    global CACHE_ARTISTAS
    if CACHE_ARTISTAS and not force_refresh: return CACHE_ARTISTAS

    if memoria:
        try:
            # Tenta conectar sem travar o boot
            if not memoria.collection: 
                try: memoria._conectar()
                except: pass
            
            if memoria.collection:
                dados = memoria.collection.get(include=['metadatas'])
                novos_artistas = set()
                if dados and 'metadatas' in dados:
                    for meta in dados['metadatas']:
                        nome = meta.get('artista')
                        if nome:
                            partes = re.split(r',|&| feat\. | ft\. ', nome, flags=re.IGNORECASE)
                            for p in partes:
                                if len(p.strip()) > 2: novos_artistas.add(p.strip())
                
                # Manuais de segurança (Adicione seus artistas favoritos aqui para garantir match 100%)
                manuais = ["Frei Gilson", "Metallica", "Pink Floyd", "The Weeknd", "Coldplay", 
                           "Hillsong", "Oficina G3", "Guns N' Roses", "Matuê", "WIU", "Imagine Dragons",
                           "Gusttavo Lima", "One Dance", "Anti Da Menace"]
                novos_artistas.update(manuais)
                
                CACHE_ARTISTAS = list(novos_artistas)
                logger.info(f"✅ Memória Fonética: {len(CACHE_ARTISTAS)} artistas.")
        except: pass
    
    return CACHE_ARTISTAS

def analisar_intencao_musical(texto_sujo, artistas):
    """
    Analisa a frase e retorna metadados detalhados sobre a intenção musical.
    
    Retorna:
        tuple: (Melhor Candidato, Score de Confiança, Termo Original Limpo)
    """
    texto_lower = texto_sujo.lower().strip()
    
    # Verbos de comando que servem de âncora
    gatilhos = ["tocar", "reproduzir", "ouve", "ouvir", "bota", "play", "coloca", "escute", "toka"]
    
    termo_limpo = texto_lower
    gatilho_encontrado = False

    # 1. Extração do Termo (Remove o verbo e limpa a frase)
    for g in gatilhos:
        if re.search(rf"\b{g}\b", texto_lower):
            partes = texto_lower.split(g, 1)
            termo_limpo = partes[1].strip()
            gatilho_encontrado = True
            
            # Remove artigos iniciais (ex: "tocar a coldplay" -> "coldplay")
            termo_limpo = re.sub(r"^(a|o|as|os|um|uma|do|da|dos|das|no|na)\s+", "", termo_limpo).strip()
            # Remove pontuação
            termo_limpo = re.sub(r'[^\w\s]', '', termo_limpo).strip()
            break
    
    # Se não achou verbo musical, retorna score 0 para não forçar barra
    if not gatilho_encontrado:
        return termo_limpo, 0.0, termo_limpo

    # Se o termo for muito curto (ex: "a"), ignora
    if len(termo_limpo) < 2:
        return termo_limpo, 0.0, termo_limpo

    # 2. Busca Fuzzy no Banco de Dados
    # Cutoff 0.4: Pegamos até candidatos ruins para o sistema poder perguntar "Você quis dizer...?"
    matches = get_close_matches(termo_limpo, artistas, n=1, cutoff=0.4) 
    
    if matches:
        candidato = matches[0]
        # Calcula a similaridade (0.0 a 1.0)
        score = SequenceMatcher(None, termo_limpo, candidato.lower()).ratio()
        
        # Trava de Segurança: Diferença de tamanho muito grande (evita "One Dance" -> "Anti Da Menace")
        diff_len = abs(len(termo_limpo) - len(candidato))
        if diff_len > 5 and score < 0.8:
            logger.debug(f"🛡️ Candidato ignorado por diferença de tamanho: '{termo_limpo}' vs '{candidato}'")
            return termo_limpo, 0.0, termo_limpo

        return candidato, score, termo_limpo
    
    return termo_limpo, 0.0, termo_limpo

def aplicar_fuzzy(texto, mapa_correcoes, threshold_auto=0.75):
    """
    Processa o texto e retorna um DICIONÁRIO DE DECISÃO para o Orquestrador.
    
    Retorno:
    {
        "texto": str (Frase final reconstruída),
        "termo_detectado": str (O que tem no DB),
        "termo_original": str (O que foi ouvido),
        "confianca": float (0.0 a 1.0),
        "origem": str ("manual" | "fuzzy" | "raw")
    }
    """
    if not texto: 
        return {"texto": "", "confianca": 0, "origem": "raw"}
    
    texto_final = texto
    
    # 1. Correção Manual Direta (JSON) - Confiança Absoluta (1.0)
    # Isso tem prioridade máxima. Se está no JSON, o usuário ensinou.
    if mapa_correcoes:
        for errado, correto in mapa_correcoes.items():
            if errado in texto_final.lower():
                pattern = re.compile(re.escape(errado), re.IGNORECASE)
                texto_final = pattern.sub(correto, texto_final)
                
                # Se houve alteração, retornamos como correção manual
                if texto_final != texto:
                    return {
                        "texto": texto_final,
                        "termo_detectado": correto,
                        "termo_original": errado, # Aproximação
                        "confianca": 1.0,
                        "origem": "manual"
                    }

    # 2. Análise Musical Inteligente (Fuzzy Logic)
    artistas = carregar_memoria_artistas()
    candidato, score, termo_extraido = analisar_intencao_musical(texto_final, artistas)
    
    # Lógica de Decisão do Texto Final:
    # Se a confiança for alta (> threshold_auto), já substituímos na frase final.
    # Se for média/baixa, mantemos o original na frase, mas enviamos os dados para o Orquestrador decidir perguntar.
    
    termo_para_frase = candidato if score >= threshold_auto else termo_extraido
    
    # Reconstrói a frase mantendo o verbo original se possível, ou padroniza
    frase_reconstruida = texto_final
    
    # Tenta substituir o termo extraído pelo candidato (se aprovado)
    if termo_extraido and termo_extraido in texto_final.lower():
        # Substituição case-insensitive simples
        start_idx = texto_final.lower().find(termo_extraido)
        if start_idx != -1:
            frase_reconstruida = texto_final[:start_idx] + termo_para_frase + texto_final[start_idx+len(termo_extraido):]
    elif "tocar" in texto_final.lower():
        # Fallback de reconstrução
        frase_reconstruida = f"Jarvis tocar {termo_para_frase}"

    return {
        "texto": frase_reconstruida.strip(),
        "termo_detectado": candidato,     # Sugestão do DB (ex: Coldplay)
        "termo_original": termo_extraido, # O que foi ouvido (ex: codeplay)
        "confianca": score,               # Nível de certeza
        "origem": "fuzzy"
    }

# Wrapper para compatibilidade com chamadas antigas que esperam apenas string
# (Opcional, mas recomendado se houver outros módulos usando este arquivo)
def analisar_comando(texto):
    # Por padrão, carrega o mapa do módulo reflexos (se injetado) ou vazio
    # Aqui assumimos que quem chama vai passar o mapa, ou usamos o aplicar_fuzzy diretamente
    return aplicar_fuzzy(texto, {})