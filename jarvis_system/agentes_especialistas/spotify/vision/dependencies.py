import logging

logger = logging.getLogger("VISION_DEPS")

# Tenta importar bibliotecas pesadas de visão
try:
    import cv2
    import easyocr
    import numpy as np
    from thefuzz import fuzz
    DEPENDENCIES_OK = True
except ImportError as e:
    logger.warning(f"⚠️ Dependências visuais ausentes ou incompletas: {e}")
    DEPENDENCIES_OK = False
    # Mock das bibliotecas para evitar NameError no resto do código
    cv2 = None
    easyocr = None
    np = None
    fuzz = None