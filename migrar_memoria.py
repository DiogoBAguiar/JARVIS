import os
import sys
import re
from typing import Optional, Tuple

# Garante raiz do projeto
sys.path.append(os.getcwd())

from jarvis_system.hipocampo.memoria import memoria
from jarvis_system.cortex_frontal.observability import JarvisLogger

log = JarvisLogger("MIGRADOR_EXPLORER")

# Padrões de captura baseados no histórico das versões anteriores (V3 a V7)
PADROES_MUSICA = [
    re.compile(r"música ['\"](.+?)['\"] de ['\"](.+?)['\"]", re.IGNORECASE),
    re.compile(r"curte a música ['\"](.+?)['\"] de ['\"](.+?)['\"]", re.IGNORECASE),
    re.compile(r"Gosto:\s*(.+?)\s+de\s+(.+)", re.IGNORECASE),
]

def extrair_musica(documento: str) -> Optional[Tuple[str, str]]:
    for padrao in PADROES_MUSICA:
        match = padrao.search(documento)
        if match:
            return match.group(1).strip(), match.group(2).strip()
    return None

def migrar_base_de_dados(dry_run: bool = False) -> None:
    log.info("🚀 Iniciando migração com inspeção de coleções...")

    if not memoria._conectar():
        log.critical("🛑 Erro ao conectar no Hipocampo.")
        return

    # 1. INSPEÇÃO: Lista todas as coleções disponíveis no banco físico
    colecoes_existentes = memoria.client.list_collections()
    nomes_colecoes = [c.name for c in colecoes_existentes]
    log.info(f"🔍 Coleções detectadas no ChromaDB: {nomes_colecoes}")

    if not nomes_colecoes:
        log.warning("❌ Nenhuma coleção encontrada no banco de dados físico.")
        return

    migrados_total = 0

    # 2. ITERAÇÃO: Busca dados em cada coleção encontrada
    for nome_col in nomes_colecoes:
        log.info(f"📂 Processando coleção: '{nome_col}'...")
        col = memoria.client.get_collection(name=nome_col)
        dados = col.get()
        documentos = dados.get("documents", [])

        if not documentos:
            log.info(f"   - Coleção '{nome_col}' está vazia.")
            continue

        log.info(f"   - {len(documentos)} documentos encontrados em '{nome_col}'.")

        for idx, doc in enumerate(documentos, start=1):
            try:
                resultado = extrair_musica(doc)
                if resultado:
                    musica, artista = resultado
                    if not dry_run:
                        # Salva na coleção OFICIAL usando o novo formato de metadados
                        memoria.memorizar_musica(
                            musica=musica, 
                            artista=artista, 
                            tags="spotify_likes"
                        )
                    migrados_total += 1
            except Exception as e:
                log.error(f"   - Erro no documento {idx} de {nome_col}: {e}")

    log.info(f"✅ Fim da migração. Total de músicas recuperadas: {migrados_total}")
    log.info(f"📡 Status Final: {memoria.status()}")

if __name__ == "__main__":
    # DICA: Mude para True primeiro para testar se ele acha as músicas
    migrar_base_de_dados(dry_run=True)