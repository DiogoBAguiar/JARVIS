import logging
import json
import sys
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Any, Dict, Optional

# Cores ANSI para o Terminal
RESET = "\033[0m"
BOLD = "\033[1m"
COLORS = {
    'DEBUG': "\033[36m",    # Cyan
    'INFO': "\033[32m",     # Green
    'WARNING': "\033[33m",  # Yellow
    'ERROR': "\033[31m",    # Red
    'CRITICAL': "\033[41m"  # Red Background
}

class ColorFormatter(logging.Formatter):
    """Adiciona cores ao log baseado no nível de severidade."""
    def format(self, record):
        color = COLORS.get(record.levelname, RESET)
        # Formato: Hora - [NIVEL] - Modulo - Mensagem
        log_fmt = f"{RESET}%(asctime)s - {color}[%(levelname)s]{RESET} - {BOLD}%(name)s{RESET} - %(message)s"
        formatter = logging.Formatter(log_fmt, datefmt='%H:%M:%S')
        return formatter.format(record)

class JarvisLogger:
    """
    Logger estruturado do Sistema Jarvis.
    Recursos:
    1. Console Colorido (DX - Developer Experience).
    2. Arquivo Rotativo (Forensics - Mantém histórico sem lotar disco).
    3. Contexto Estruturado (JSON metadata).
    """
    
    def __init__(self, module_name: str):
        self.logger = logging.getLogger(module_name)
        self.logger.setLevel(logging.DEBUG) # Captura tudo, os handlers filtram
        
        # Evita duplicidade de logs se o módulo for importado várias vezes
        if not self.logger.handlers:
            self._setup_console_handler()
            self._setup_file_handler()

    def _setup_console_handler(self):
        """Saída para o terminal (Colorida e Concisa)."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO) # No terminal, mostramos apenas o essencial
        console_handler.setFormatter(ColorFormatter())
        self.logger.addHandler(console_handler)

    def _setup_file_handler(self):
        """Saída para arquivo (Detalhada e Persistente)."""
        # Garante que a pasta de logs existe
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        log_dir = os.path.join(base_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, "jarvis_system.log")
        
        # Roda o arquivo quando atingir 5MB, mantém 3 backups
        file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG) # No arquivo, guardamos tudo (inclusive debug)
        
        formatter = logging.Formatter(
            '%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def _format_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Formata a mensagem e anexa contexto JSON se houver."""
        if context:
            try:
                # default=str garante que objetos como datetime não quebrem o JSON
                context_str = json.dumps(context, default=str, ensure_ascii=False)
                return f"{message} | ctx: {context_str}"
            except Exception:
                return f"{message} | ctx: [SERIALIZATION_ERROR]"
        return message

    def debug(self, message: str, **context):
        self.logger.debug(self._format_message(message, context))

    def info(self, message: str, **context):
        self.logger.info(self._format_message(message, context))

    def warning(self, message: str, **context):
        self.logger.warning(self._format_message(message, context))

    def error(self, message: str, exc_info=True, **context):
        """
        Logs de erro devem incluir stacktrace (exc_info=True) por padrão
        para facilitar o debugging.
        """
        self.logger.error(self._format_message(message, context), exc_info=exc_info)

    def critical(self, message: str, exc_info=True, **context):
        """Erros fatais que indicam instabilidade sistêmica."""
        msg = self._format_message(f"🛑 SISTEMA CRÍTICO: {message}", context)
        self.logger.critical(msg, exc_info=exc_info)