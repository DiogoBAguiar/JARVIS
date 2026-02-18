import logging

try:
    from .hipocampoReflexos import HipocampoReflexos
    # Instância Singleton pronta para uso
    reflexos = HipocampoReflexos()
except Exception as e:
    logging.getLogger("REFLEXOS_INIT").error(f"Erro ao iniciar pacote: {e}")
    reflexos = None