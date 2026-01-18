# Expõe a classe de aprendizado offline (Compatibilidade com main.py)
from .dreamer import Subconsciente

# Expõe a classe de interação online (Para o Orchestrator)
from .dreamer import DayDreamer

# Instancia o 'sonhador diurno' e exporta como 'curiosity'
# Isso permite que o Orchestrator faça: 'from ...subconsciente import curiosity'
curiosity = DayDreamer()