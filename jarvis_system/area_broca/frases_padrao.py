import random

# Dicionário com todas as suas frases categorizadas
FRASES_DO_SISTEMA = {
    "ALERTA": [
        "Acesso não autorizado",
        "Alerta de segurança intrusão detectada",
        "Alerta de segurança risco detectado",
        "Atenção formação de gelo em nível",
        "Atenção senhor algo saiu do previsto",
        "Recomendo cautela imediata",
        "Senhor não vamos conseguir",
        "Superaquecimento iminente recomendo cautela"
    ],
    "BOAS_VINDAS": [
        "Bemvindo de volta",
        "Bemvindo de volta senhor senti sua",
        "Boa noite posso auxiliálo com algo",
        "Boa noite senhor deseja revisar algo",
        "Boa tarde senhor em que posso",
        "Boa tarde seus sistemas estão estáveis",
        "Bom dia senhor o que deseja",
        "Bom dia senhor todos os sistemas",
        "Conexão restabelecida aguardando seus comandos",
        "Em que posso ser útil hoje",
        "Jarvis online senhor como posso ser útil",  
        "Pronto para servilo",
        "Sempre ao seu dispor senhor",
        "Sessão retomada pronto para continuar de",
        "É um prazer estar online"
    ],
    "COMBATE": [
        "Alvos adquiridos",
        "Ativando sistemas de defesa",
        "Senhor cuidado à esquerda",
        "Zona hostil confirmada"
    ],
    "CONFIRMACAO": [
        "Como desejar iniciando procedimento",
        "Entendido senhor executando agora",
        "Execução concluída com sucesso",
        "Solicitação recebida processando",
        "Tarefa em andamento"
    ],
    "ERRO_SISTEMA": [
        "Detectei uma anomalia nos processos",
        "Erro crítico reiniciando subsistemas afetados",
        "Falha na renderização dos dados",
        "Houve um erro interno ao tentar",
        "Os servidores não estão respondendo",
        "Perda de conexão estamos offline",
        "Senhor algo deu errado no sistema"
    ],
    "HUMOR": [
        "Ah sim uma ideia brilhante estatisticamente falando",
        "Claro senhor o caos é apenas uma variável",
        "Claro vamos fingir que isso vai dar certo",
        "Estatisticamente falando isso não vai dar certo",
        "Excelente escolha senhor",
        "Ha ha ha muito engraçado senhor",
        "Se der errado eu aviso que avisei",
        "Senhor tente não morrer dessa vez"
    ],
    "STATUS": [
        "Bateria em quarenta por cento e caindo",
        "Diagnósticos indicam funcionamento nominal em todos os setores",
        "Nenhuma anomalia detectada até o momento",
        "Pronto para iniciar novas tarefas",
        "Todos os sistemas estão operacionais"
    ]
}

def obter_frase(categoria):
    """Retorna uma frase aleatória da categoria solicitada."""
    # Remove colchetes se vierem na string (ex: [[ALERTA]] -> ALERTA)
    clean_cat = categoria.replace("[[", "").replace("]]", "").strip()
    
    if clean_cat in FRASES_DO_SISTEMA:
        return random.choice(FRASES_DO_SISTEMA[clean_cat])
    return None