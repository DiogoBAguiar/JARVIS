import datetime
from .base_agente import AgenteEspecialista

# Simulação de Banco de Dados (depois trocamos por Google Calendar ou arquivo .db)
EVENTOS_MOCK = []

class AgenteCalendario(AgenteEspecialista):
    @property
    def nome(self):
        return "calendario"

    @property
    def gatilhos(self):
        return ["agendar", "marcar", "compromisso", "reunião", "agenda", "calendário"]

    def executar(self, comando: str, **kwargs) -> str:
        comando = comando.lower()
        
        # 1. Adicionar Evento
        if any(w in comando for w in ["agendar", "marcar", "adicionar"]):
            # Aqui você pode usar o LLM depois para extrair a data exata
            # Por enquanto, vamos fazer um mock simples
            evento = comando.replace("agendar", "").replace("marcar", "").strip()
            data_hora = datetime.datetime.now().strftime("%d/%m às %H:%M")
            
            EVENTOS_MOCK.append(f"{evento} - (Criado em {data_hora})")
            return f"Agendado: '{evento}' no seu calendário."

        # 2. Ler Eventos
        elif any(w in comando for w in ["ler", "quais", "tenho", "mostra"]):
            if not EVENTOS_MOCK:
                return "Sua agenda está vazia por enquanto."
            
            lista = "\n".join([f"- {e}" for e in EVENTOS_MOCK])
            return f"Aqui estão seus compromissos:\n{lista}"

        return "Desculpe, sou o especialista de calendário, mas não entendi o que fazer com a agenda."