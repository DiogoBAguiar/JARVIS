# jarvis_system/cortex_frontal/orchestrator/config.py

# Palavras que ativam o sistema
WAKE_WORDS = ["jarvis", "jarbas", "computer", "sexta-feira", "javis", "jardis"]

# Comandos de Confirmação (Reflexo rápido)
CONFIRMATION_YES = ["sim", "pode", "pode ser", "isso", "vai", "confirma", "abre", "ok", "claro", "positivo"]
CONFIRMATION_NO = ["não", "cancela", "errado", "esquece", "nada a ver", "negativo"]

# Gatilhos de Memória Explícita
MEMORY_TRIGGERS = ["memorize", "memoriza", "aprenda", "aprende", "grave", "lembre-se", "anote"]

# Tempo (segundos) que o Jarvis mantém o contexto ativo após um comando
ATTENTION_WINDOW = 40.0