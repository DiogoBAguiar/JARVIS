from typing import Optional
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos
# Importa o registro para poder consultar/executar ferramentas
from jarvis_system.cortex_motor.tool_registry import registry

log = JarvisLogger("CORTEX_ORCHESTRATOR")

class Orchestrator:
    def __init__(self):
        bus.inscrever(Eventos.FALA_RECONHECIDA, self._processar_intencao)
        log.info("Córtex Frontal Online: Pronto para tomada de decisão.")

    def _processar_intencao(self, evento: Evento):
        texto_bruto = evento.dados.get("texto", "")
        comando = texto_bruto.lower().strip()
        
        log.info(f"Analisando intenção: '{comando}'")

        if not comando:
            return

        # --- CAMADA 1: Comandos de Sistema (Prioridade Máxima) ---
        if self._verificar_ferramentas_diretas(comando):
            return

        # --- CAMADA 2: Fallback (Chat/LLM Futuro) ---
        self._responder(f"Comando '{comando}' não reconhecido nos protocolos atuais.")

    def _verificar_ferramentas_diretas(self, comando: str) -> bool:
        """
        Tenta mapear a fala do usuário diretamente para uma ferramenta registrada.
        Lógica Simples (Keyword Matching) por enquanto.
        """
        
        # Mapeamento Fala -> ID da Ferramenta
        # No futuro, isso será feito por LLM (Function Calling)
        mapa_intencoes = {
            "calculadora": "abrir_calculadora",
            "contas": "abrir_calculadora",
            "bloco de notas": "abrir_bloco_notas",
            "anotar": "abrir_bloco_notas",
            "status": "sistema_ping", # Usando aquele ping que criamos antes
            "desligar": "sistema_desligar"
        }

        for palavra_chave, tool_name in mapa_intencoes.items():
            if palavra_chave in comando:
                log.info(f"Intenção detectada: {tool_name}")
                
                try:
                    # Executa a ferramenta
                    resultado = registry.execute(tool_name)
                    
                    # Tratamento especial para desligamento
                    if resultado == "__SHUTDOWN_SIGNAL__":
                        self._responder("Desligando sistemas. Até logo.")
                        bus.publicar(Evento(Eventos.SHUTDOWN, {})) # Aviso global
                        # Em produção, teríamos um handler de shutdown gracioso
                        import sys; sys.exit(0)
                    
                    # Resposta padrão
                    self._responder(f"Executado: {resultado}")
                    return True
                    
                except Exception as e:
                    self._responder(f"Tentei executar {tool_name}, mas falhei.")
                    return True
        
        return False

    def _responder(self, texto: str):
        bus.publicar(Evento(Eventos.FALAR, {"texto": texto}))

brain = Orchestrator()