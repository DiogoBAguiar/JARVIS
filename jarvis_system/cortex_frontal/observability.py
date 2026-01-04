import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional

class JarvisLogger:
    """
    Logger estruturado oficial do Sistema Jarvis.
    
    Adere ao princípio Big Tech de observabilidade:
    - Logs devem ser parsáveis por máquina (JSON em produção).
    - Logs devem conter contexto (quem chamou, latência, custo).
    - Nunca use print() em produção.
    """
    
    def __init__(self, module_name: str):
        self.logger = logging.getLogger(module_name)
        self.logger.setLevel(logging.DEBUG)
        
        # Evita duplicação de handlers se instanciado múltiplas vezes
        if not self.logger.handlers:
            # Handler para Console (Dev friendly)
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _format_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Formata a mensagem. Futuramente pode virar JSON puro."""
        if context:
            # Em Big Tech, logs carregam metadados (tokens, latência, user_id)
            return f"{message} | CONTEXT: {json.dumps(context, default=str)}"
        return message

    def info(self, message: str, **context):
        self.logger.info(self._format_message(message, context))

    def error(self, message: str, exc_info=True, **context):
        """Erros devem sempre ter stacktrace (exc_info=True por padrão)."""
        self.logger.error(self._format_message(message, context), exc_info=exc_info)

    def warning(self, message: str, **context):
        self.logger.warning(self._format_message(message, context))

    def debug(self, message: str, **context):
        self.logger.debug(self._format_message(message, context))

    # --- [NOVO] Adicionado para corrigir o erro do listen.py ---
    def critical(self, message: str, exc_info=True, **context):
        """Erros críticos que podem derrubar a aplicação."""
        # Adiciona um ícone visual para destacar no console
        msg_formatada = self._format_message(f"🛑 FATAL: {message}", context)
        self.logger.critical(msg_formatada, exc_info=exc_info)

# Instância Singleton para importação rápida se necessário, 
# mas prefira instanciar por módulo.