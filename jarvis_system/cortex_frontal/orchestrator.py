import time
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos
from jarvis_system.cortex_motor.tool_registry import registry
# Importa o Cérebro Híbrido (que já tem o Hipocampo dentro)
from jarvis_system.cortex_frontal.brain_llm import llm 

log = JarvisLogger("CORTEX_ORCHESTRATOR")

# Tempo (em segundos) que o Jarvis mantém o contexto sem precisar ouvir o nome de novo
WINDOW_ATENCAO = 30.0

class Orchestrator:
    def __init__(self):
        bus.inscrever(Eventos.FALA_RECONHECIDA, self._processar_intencao)
        self._ultima_ativacao = 0.0
        log.info("Córtex Frontal v4 (Full Stack + Tolerância Fonética).")

    def _processar_intencao(self, evento: Evento):
        texto_bruto = evento.dados.get("texto", "")
        if not texto_bruto: return

        # Normalização básica
        comando = texto_bruto.lower().replace(".", "").replace(",", "").replace("?", "").strip()
        
        # --- FASE 1: Detecção de Wake Word ---
        wake_words = ["jarvis", "jarbas", "computer"]
        detectou_wake = False
        comando_limpo = comando
        
        for w in wake_words:
            if comando.startswith(w):
                detectou_wake = True
                # Remove o nome para processar o comando limpo
                # Ex: "jarvis abrir calc" -> "abrir calc"
                comando_limpo = comando.replace(w, "", 1).strip()
                break
        
        if detectou_wake:
            self._ultima_ativacao = time.time()
            log.info(f">> WAKE WORD CONFIRMADA. Comando: '{comando_limpo}'")
            
            # Se o usuário falou apenas "Jarvis", damos feedback e aguardamos
            if not comando_limpo:
                self._responder("Às ordens.")
                return

        # --- FASE 2: Janela de Contexto (Short-Term Memory) ---
        tempo_passado = time.time() - self._ultima_ativacao
        esta_atento = tempo_passado < WINDOW_ATENCAO

        if not esta_atento:
            log.debug(f"Ignorado (Sem Atenção): {comando}")
            return

        # --- FASE 3: Filtro de Ruído ---
        # Ignora frases muito curtas que não começam com Wake Word (provavelmente eco ou ruído)
        if len(comando) < 4 and not detectou_wake:
            log.debug(f"Ignorado (Ruído/Muito Curto): '{comando}'")
            return

        # --- FASE 4: Execução de Ferramentas (Mecânicas + Memória) ---
        # Tenta resolver internamente antes de gastar tokens da IA
        if self._verificar_ferramentas_diretas(comando_limpo):
            return

        # --- FASE 5: Inteligência Artificial (LLM + Hipocampo) ---
        # Se não é comando mecânico, é conversa ou pergunta complexa
        log.info(f"Encaminhando para Cérebro Híbrido: {comando_limpo}")
        
        # Feedback visual
        print(f"[IA PENSANDO]: {comando_limpo}...")
        
        # O brain_llm.py vai consultar o Hipocampo e depois a Groq
        resposta = llm.pensar(comando_limpo)
        self._responder(resposta)

    def _verificar_ferramentas_diretas(self, comando: str) -> bool:
        """
        Verifica comandos explícitos: Memória (Escrita) e Ferramentas (Motoras).
        """
        
        # 1. Comandos de Aprendizado (Hipocampo Escrita)
        # Lista expandida para pegar erros fonéticos do Vosk (ex: 'aprendeis')
        gatilhos_memoria = [
            "memorize", "memoriza", 
            "aprenda", "aprende", "aprendeis", 
            "grave", "grava", 
            "lembre-se", "lembre",
            "anote"
        ]
        
        for gatilho in gatilhos_memoria:
            # Verifica se o gatilho está presente na frase
            if gatilho in comando:
                # Divide a frase usando o gatilho como separador
                # Ex: "jarvis aprendeis que hoje é sabado" -> ["", " que hoje é sabado"]
                partes = comando.split(gatilho, 1)
                
                if len(partes) > 1:
                    fato = partes[1].strip()
                    
                    # Limpeza inteligente de conectivos pós-verbo
                    # Remove "que", "isso", ":" do início do fato para salvar limpo
                    if fato.startswith("que "):
                        fato = fato[4:].strip()
                    elif fato.startswith("isso "):
                        fato = fato[5:].strip()
                    elif fato.startswith(":"):
                        fato = fato[1:].strip()
                    
                    if fato:
                        log.info(f"Comando de Memória detectado: '{fato}'")
                        resultado = llm.ensinar(fato)
                        self._responder("Memória arquivada no Hipocampo.")
                        return True
                    else:
                        self._responder("O que devo memorizar?")
                        return True

        # 2. Comandos Mecânicos (Tool Registry)
        mapa_intencoes = {
            "calculadora": "abrir_calculadora",
            "bloco de notas": "abrir_bloco_notas", 
            "notepad": "abrir_bloco_notas",
            "status": "sistema_ping",
            "ping": "sistema_ping",
            "desligar": "sistema_desligar",
            "encerrar": "sistema_desligar"
        }

        for palavra_chave, tool_name in mapa_intencoes.items():
            if palavra_chave in comando:
                log.info(f"Executando ferramenta mecânica: {tool_name}")
                try:
                    resultado = registry.execute(tool_name)
                    
                    # Tratamento especial para desligamento
                    if resultado == "__SHUTDOWN_SIGNAL__":
                        self._responder("Desligando sistemas.")
                        bus.publicar(Evento(Eventos.SHUTDOWN, {}))
                        import sys; sys.exit(0)
                    
                    self._responder(f"{resultado}")
                    return True
                except Exception as e:
                    self._responder(f"Erro ao executar ferramenta: {str(e)}")
                    return True
                    
        return False

    def _responder(self, texto: str):
        # Publica no barramento para que a Área de Broca (Voz) fale
        bus.publicar(Evento(Eventos.FALAR, {"texto": texto}))

brain = Orchestrator()