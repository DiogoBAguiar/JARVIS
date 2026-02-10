import json
import random
import os
from datetime import datetime
from typing import Optional, Dict

# --- CONFIGURAÇÃO DE CAMINHOS ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "jarvis_system", "data", "voices", "voice_index.json"))

def _carregar_indice() -> Dict:
    if not os.path.exists(INDEX_PATH):
        alt_path = os.path.join(os.getcwd(), "jarvis_system", "data", "voices", "voice_index.json")
        if os.path.exists(alt_path):
            try:
                with open(alt_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: return {}
        return {}
    
    try:
        with open(INDEX_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao ler voice_index.json: {e}")
        return {}

def _get_contexto_temporal() -> str:
    hora = datetime.now().hour
    if 5 <= hora < 12: return "morning"
    elif 12 <= hora < 18: return "afternoon"
    else: return "night"

def obter_frase(categoria: str, forcar_sub_contexto: str = None) -> Optional[str]:
    """
    Seletor Hierárquico com Debug no Console.
    """
    clean_cat = categoria.replace("[[", "").replace("]]", "").strip().upper()
    
    dados = _carregar_indice()
    if not dados:
        print(f"⚠️ [FRASES] Banco de dados vazio ou não encontrado.")
        return None 

    candidatos_perfeitos = [] # Bate Tempo E Sub-contexto
    candidatos_genericos = [] # Bate Sub-contexto mas Tempo é "any"
    
    contexto_atual = _get_contexto_temporal()
    
    # DEBUG: Mostra o que o sistema está buscando
    print(f"🔍 [SELETOR] Buscando: Cat='{clean_cat}' | Hora='{contexto_atual}' | Sub='{forcar_sub_contexto}'")

    for key, metadata in dados.items():
        if not isinstance(metadata, dict): continue
        
        # 1. Filtro de Categoria
        if metadata.get("category") != clean_cat:
            continue

        # 2. Filtro de Sub-contexto (Se solicitado)
        if forcar_sub_contexto:
            if metadata.get("sub_context") != forcar_sub_contexto:
                continue

        texto = metadata.get("text")
        ctx_frase = metadata.get("context", "any")
        
        if not texto: continue

        # Classificação
        if ctx_frase == contexto_atual:
            candidatos_perfeitos.append(texto)
        elif ctx_frase == "any":
            candidatos_genericos.append(texto)

    # DEBUG: Mostra o resultado da busca
    print(f"   📊 Encontrados: {len(candidatos_perfeitos)} Perfeitos (Prioridade) | {len(candidatos_genericos)} Genéricos (Fallback)")

    # Lógica de Prioridade:
    if candidatos_perfeitos:
        escolhida = random.choice(candidatos_perfeitos)
        print(f"   ✅ Selecionado (Perfeito): '{escolhida[:30]}...'")
        return escolhida
    
    if candidatos_genericos:
        escolhida = random.choice(candidatos_genericos)
        print(f"   ⚠️ Selecionado (Genérico - Fallback): '{escolhida[:30]}...'")
        return escolhida
    
    print("   ❌ Nenhuma frase encontrada.")
    return None