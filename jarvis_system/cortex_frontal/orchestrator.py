import time
import re
import sys
import random

# Imports do Sistema
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos

# Ferramentas Motoras
from jarvis_system.cortex_motor.tool_registry import registry
from jarvis_system.cortex_motor.launcher import launcher 

# Inteligência (Cérebro + Subconsciente)
from jarvis_system.cortex_frontal.brain_llm import llm 
from jarvis_system.cortex_frontal.subconsciente import curiosity

log = JarvisLogger("CORTEX_ORCHESTRATOR")

# Tempo (em segundos) que o Jarvis mantém a conversa ativa
WINDOW_ATENCAO = 30.0

class Orchestrator:
    def __init__(self):
        bus.inscrever(Eventos.FALA_RECONHECIDA, self._processar_intencao)
        self._ultima_ativacao = 0.0
        
        # --- MEMÓRIA DE ESTADO (Short-Term State) ---
        # Guarda o contexto imediato, como um app esperando confirmação para abrir
        # Formato: {"nome": "visual studio", "caminho": "..."}
        self.app_pendente = None  
        
        log.info("Córtex Frontal v6 (Stateful + Curiosity + Launcher).")

    def _processar_intencao(self, evento: Evento):
        try:
            texto_bruto = evento.dados.get("texto", "")
            if not texto_bruto: return

            # Normalização (remove pontuação)
            comando = re.sub(r'[^\w\s]', '', texto_bruto.lower()).strip()
            
            # --- FASE 0: Verifica se é RESPOSTA a uma pendência (Sim/Não) ---
            # Isso acontece antes da Wake Word para permitir fluidez ("Sim, pode abrir")
            if self.app_pendente:
                if self._verificar_confirmacao(comando):
                    # Se processou a confirmação, atualiza o tempo de atenção e sai
                    self._ultima_ativacao = time.time()
                    return 
            
            # --- FASE 1: Detecção de Wake Word ---
            wake_words = ["jarvis", "jarbas", "computer", "sexta-feira"]
            detectou_wake = False
            comando_limpo = comando
            
            for w in wake_words:
                if comando.startswith(w):
                    detectou_wake = True
                    comando_limpo = comando[len(w):].strip()
                    break
            
            if detectou_wake:
                self._ultima_ativacao = time.time()
                log.info(f">> COMANDO: '{comando_limpo}'")
                
                if not comando_limpo:
                    self._responder("Pois não?")
                    return

            # --- FASE 2: Janela de Contexto ---
            tempo_passado = time.time() - self._ultima_ativacao
            esta_atento = tempo_passado < WINDOW_ATENCAO

            if not detectou_wake and not esta_atento:
                return
            
            if esta_atento and not detectou_wake:
                self._ultima_ativacao = time.time()

            # Filtro de ruído para frases muito curtas sem wake word
            if len(comando) < 3 and not detectou_wake: return

            # --- FASE 4: Execução de Ferramentas (Launcher, Memória, Sistema) ---
            if self._verificar_ferramentas_diretas(comando_limpo):
                return

            # --- FASE 5: Inteligência Artificial (LLM + Subconsciente) ---
            # Se não é comando nem confirmação, é conversa
            self.app_pendente = None # Limpa pendência antiga se mudou de assunto
            
            log.info(f"Thinking: {comando_limpo}")
            
            # 1. Resposta Padrão (Cérebro Operário)
            resposta_principal = llm.pensar(comando_limpo)
            texto_final = resposta_principal

            # 2. Ativação do Subconsciente (Cérebro Curioso)
            # Chance de 30% OU se a resposta for muito curta, ele tenta puxar assunto
            chance_curiosidade = random.random() < 0.3 
            resposta_curta = len(resposta_principal.split()) < 6
            
            if chance_curiosidade or resposta_curta:
                pergunta_extra = curiosity.gerar_pergunta(comando_limpo)
                if pergunta_extra:
                    log.info(f"Subconsciente disparou: '{pergunta_extra}'")
                    # Adiciona a pergunta ao final da fala
                    texto_final = f"{resposta_principal} ... Ah, e {pergunta_extra}"

            self._responder(texto_final)
            
        except Exception as e:
            log.error(f"Erro crítico no Orchestrator: {e}")
            self._responder("Ocorreu um erro no meu processamento central.")

    def _verificar_confirmacao(self, comando: str) -> bool:
        """
        Verifica se o usuário respondeu SIM ou NÃO para a sugestão pendente.
        """
        sim_words = ["sim", "pode", "pode ser", "isso", "vai", "confirma", "abre", "ok", "claro", "positivo"]
        nao_words = ["não", "cancela", "errado", "esquece", "nada a ver", "negativo"]

        # Verifica SIM
        if any(w in comando for w in sim_words):
            app = self.app_pendente
            self._responder(f"Entendido. Abrindo {app['nome']}...")
            launcher.abrir_por_caminho(app['caminho'])
            self.app_pendente = None # Limpa estado
            return True
        
        # Verifica NÃO
        elif any(w in comando for w in nao_words):
            self._responder("Tudo bem, cancelei.")
            self.app_pendente = None # Limpa estado
            return True

        return False

    def _verificar_ferramentas_diretas(self, comando: str) -> bool:
        """
        Verifica comandos de ação imediata.
        """
        
        # --- 1. LAUNCHER DE APPS (COM SUGESTÃO) ---
        if comando.startswith("abrir "):
            termo_busca = comando[6:].strip()
            
            # Busca no Launcher
            status, nome_real, caminho = launcher.buscar_candidato(termo_busca)
            
            if status == "EXATO":
                self._responder(f"Abrindo {nome_real}.")
                launcher.abrir_por_caminho(caminho)
                self.app_pendente = None
                return True
                
            elif status == "SUGESTAO":
                # MÁGICA: Não abre, PERGUNTA e guarda o ESTADO.
                self._responder(f"Não achei '{termo_busca}', mas tenho '{nome_real}'. É esse que você quer?")
                self.app_pendente = {"nome": nome_real, "caminho": caminho}
                return True
                
            else:
                self._responder(f"Não encontrei o aplicativo '{termo_busca}' instalado.")
                self.app_pendente = None
                return True

        # --- 2. COMANDOS DE MEMÓRIA (GRAVAÇÃO) ---
        gatilhos_memoria = ["memorize", "memoriza", "aprenda", "aprende", "grave", "lembre-se", "anote"]
        
        for gatilho in gatilhos_memoria:
            if gatilho in comando:
                partes = comando.split(gatilho, 1)
                if len(partes) > 1:
                    fato = partes[1].strip()
                    conectivos = ["que ", "isso ", "sobre ", ":"]
                    for c in conectivos:
                        if fato.startswith(c):
                            fato = fato[len(c):].strip()
                            break
                    
                    if fato:
                        llm.ensinar(fato)
                        self._responder("Entendido, memória arquivada.")
                        return True

        # --- 3. COMANDOS DE SISTEMA ---
        mapa_intencoes = {
            "status": "sistema_ping",
            "ping": "sistema_ping",
            "diagnostico": "sistema_ping",
            "desligar": "sistema_desligar",
            "encerrar": "sistema_desligar"
        }

        for palavra_chave, tool_name in mapa_intencoes.items():
            if palavra_chave in comando:
                try:
                    resultado = registry.execute(tool_name)
                    if resultado == "__SHUTDOWN_SIGNAL__":
                        self._responder("Desligando sistemas. Até logo.")
                        time.sleep(3) 
                        bus.publicar(Evento(Eventos.SHUTDOWN, {}))
                        sys.exit(0)
                    
                    self._responder(f"{resultado}")
                    return True
                except Exception as e:
                    self._responder("Erro ao executar comando de sistema.")
                    return True
                    
        return False

    def _responder(self, texto: str):
        bus.publicar(Evento(Eventos.FALAR, {"texto": texto}))

brain = Orchestrator()