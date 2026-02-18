import logging

try:
    from .memoriaHipocampo import MemoriaHipocampo
    # Instância Singleton para todo o sistema
    memoria = MemoriaHipocampo()
except Exception as e:
    logging.getLogger("HIPOCAMPO_INIT").error(f"Erro fatal ao iniciar memória: {e}")
    memoria = None