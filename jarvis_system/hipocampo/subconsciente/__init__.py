# Expõe a classe de aprendizado offline (Compatibilidade com main.py)
from .subconsciente import Subconsciente

# Expõe a classe de interação online (Para o Orchestrator)
from .subconsciente import DayDreamer

# Instancia o 'sonhador diurno' e exporta como 'curiosity'
# Isso permite que o Orchestrator faça: 'from ...subconsciente import curiosity'
curiosity = DayDreamer()