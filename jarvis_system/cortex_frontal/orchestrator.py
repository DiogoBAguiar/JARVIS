import time
from typing import Optional
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos
from jarvis_system.cortex_motor.tool_registry import registry

log = JarvisLogger("CORTEX_ORCHESTRATOR")

WINDOW_ATENCAO = 15.0

class Orchestrator:
    def __init__(self):
        bus.inscrever(Eventos.FALA_RECONHECIDA, self._processar_intencao)
        self._ultima_ativacao = 0.0
        log.info("Córtex Frontal Online (Confiança no Juiz Auditivo).")

    def _processar_intencao(self, evento: Evento):
        texto_bruto = evento.dados.get("texto", "")
        if not texto_bruto: return

        # Limpeza básica (Sem correções fonéticas agressivas!)
        comando = texto_bruto.lower().replace(".", "").replace(",", "").strip()
        
        log.info(f"Processando: '{comando}'")

        # --- FASE 1: Detecção de Wake Word ---
        # Agora confiamos que o listen.py já mandou "jarvis" se for para acordar.
        wake_words = ["jarvis", "jarbas", "computer"]
        
        detectou_wake = False
        comando_limpo = comando
        
        for w in wake_words:
            if comando.startswith(w):
                detectou_wake = True
                comando_limpo = comando.replace(w, "", 1).strip()
                break
        
        if detectou_wake:
            self._ultima_ativacao = time.time()
            log.info(">> WAKE WORD CONFIRMADA.")
            
            if not comando_limpo:
                self._responder("Pois não?")
                return

        # --- FASE 2: Janela de Contexto ---
        tempo_passado = time.time() - self._ultima_ativacao
        esta_atento = tempo_passado < WINDOW_ATENCAO

        if not esta_atento:
            # Se chegou "jardins da babilônia", não começa com jarvis e não estamos atentos.
            # O sistema IGNORA corretamente.
            log.debug(f"Ignorado (Sem Wake Word/Atenção): {comando}")
            return

        # --- FASE 3: Execução ---
        if self._verificar_ferramentas_diretas(comando_limpo):
            return

        if detectou_wake:
            self._responder(f"Comando desconhecido: {comando_limpo}")

    def _verificar_ferramentas_diretas(self, comando: str) -> bool:
        mapa_intencoes = {
            "calculadora": "abrir_calculadora",
            "bloco de notas": "abrir_bloco_notas", 
            "status": "sistema_ping",
            "desligar": "sistema_desligar"
        }

        for palavra_chave, tool_name in mapa_intencoes.items():
            if palavra_chave in comando:
                log.info(f"Executando: {tool_name}")
                try:
                    resultado = registry.execute(tool_name)
                    if resultado == "__SHUTDOWN_SIGNAL__":
                        self._responder("Desligando.")
                        bus.publicar(Evento(Eventos.SHUTDOWN, {}))
                        import sys; sys.exit(0)
                    
                    self._responder(f"{resultado}")
                    return True
                except Exception as e:
                    self._responder(f"Erro na execução.")
                    return True
        return False

    def _responder(self, texto: str):
        bus.publicar(Evento(Eventos.FALAR, {"texto": texto}))

brain = Orchestrator()