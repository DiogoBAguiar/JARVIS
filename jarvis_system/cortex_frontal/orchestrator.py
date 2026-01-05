import time
import re
import random
from typing import Optional, Tuple

# Imports do Sistema
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos

# --- DEPENDÊNCIAS (Injeção Tardia ou Try/Import para robustez) ---
try:
    from jarvis_system.cortex_motor.tool_registry import registry
    from jarvis_system.cortex_motor.launcher import launcher 
    from jarvis_system.cortex_frontal.brain_llm import llm 
    from jarvis_system.cortex_frontal.subconsciente import curiosity
    from jarvis_system.hipocampo.reflexos import reflexos
except ImportError:
    # Fallback para permitir testes isolados
    registry, launcher, llm, curiosity, reflexos = None, None, None, None, None

# --- CONFIGURAÇÃO COGNITIVA ---
WAKE_WORDS = ["jarvis", "jarbas", "computer", "sexta-feira"]
CONFIRMATION_YES = ["sim", "pode", "pode ser", "isso", "vai", "confirma", "abre", "ok", "claro", "positivo"]
CONFIRMATION_NO = ["não", "cancela", "errado", "esquece", "nada a ver", "negativo"]
MEMORY_TRIGGERS = ["memorize", "memoriza", "aprenda", "aprende", "grave", "lembre-se", "anote"]
ATTENTION_WINDOW = 30.0  # Segundos

class Orchestrator:
    def __init__(self):
        self.log = JarvisLogger("CORTEX_FRONTAL")
        self._ultima_ativacao = 0.0
        
        # Estado Volátil (Short-Term Memory)
        self.contexto_pendente: Optional[dict] = None  
        
        # Inscrição no Barramento
        bus.inscrever(Eventos.FALA_RECONHECIDA, self.processar_input)
        
        self.log.info("🧠 Córtex Frontal Inicializado (Pipeline v2.3 - Feedback Imediato).")

    def start(self):
        pass

    def stop(self):
        pass

    def processar_input(self, evento: Evento):
        """Entrada bruta do 'Ouvido'."""
        try:
            texto_bruto = evento.dados.get("texto", "")
            if not texto_bruto: return

            # 1. Normalização
            comando_limpo = re.sub(r'[^\w\s]', '', texto_bruto.lower()).strip()
            
            # 2. Pipeline de Decisão
            if self._handle_confirmation(comando_limpo): return
            
            is_wake, texto_payload = self._check_attention(comando_limpo)
            if not is_wake: return # Ignora ruído fora da janela de atenção

            # --- AJUSTE CRÍTICO: RESPOSTA AO CHAMADO ---
            # Se o usuário disse apenas "Jarvis", o payload é vazio.
            # Respondemos imediatamente para dar feedback de atenção.
            if not texto_payload:
                saudacoes = ["Pois não?", "Estou aqui.", "Sim, senhor?", "Em que posso ajudar?"]
                self._falar(random.choice(saudacoes))
                self._ultima_ativacao = time.time()
                return
            # --------------------------------------------

            # Atualiza "foco"
            self._ultima_ativacao = time.time()
            self.log.info(f"🤔 Processando: '{texto_payload}'")

            if self._handle_system_commands(texto_payload): return
            if self._handle_tools(texto_payload): return
            if self._handle_cognition(texto_payload): return

        except Exception as e:
            self.log.error(f"Erro no processamento cognitivo: {e}")
            self._falar("Ocorreu um erro interno nos meus circuitos.")

    # --- ETAPA 1: ATENÇÃO & WAKE WORD ---
    def _check_attention(self, texto: str) -> Tuple[bool, str]:
        for w in WAKE_WORDS:
            if texto.startswith(w):
                payload = texto[len(w):].strip()
                return True, payload

        tempo_passado = time.time() - self._ultima_ativacao
        if tempo_passado < ATTENTION_WINDOW:
            return True, texto

        return False, ""

    # --- ETAPA 2: REFLEXO (Confirmações com Aprendizado) ---
    def _handle_confirmation(self, texto: str) -> bool:
        if not self.contexto_pendente:
            return False

        # Verifica SIM
        if any(w in texto.split() for w in CONFIRMATION_YES):
            cmd_type = self.contexto_pendente.get("tipo")
            
            if cmd_type == "confirmar_app_learning":
                dados = self.contexto_pendente
                self._falar(f"Entendido. Abrindo {dados['alvo_real']} e aprendendo.")
                
                # 1. Executa
                if launcher: launcher.abrir_por_caminho(dados['caminho'])
                
                # 2. Aprende
                if reflexos:
                    termo_erro = dados['termo_original'].split()[0]
                    nome_app = dados['alvo_real'].lower()
                    reflexos.aprender(termo_erro, nome_app)
            
            elif cmd_type == "abrir_app":
                app = self.contexto_pendente["dados"]
                self._falar(f"Iniciando {app['nome']}...")
                if launcher: launcher.abrir_por_caminho(app['caminho'])
            
            self.contexto_pendente = None
            self._ultima_ativacao = time.time()
            return True

        # Verifica NÃO
        elif any(w in texto.split() for w in CONFIRMATION_NO):
            self._falar("Cancelado.")
            self.contexto_pendente = None
            self._ultima_ativacao = time.time()
            return True

        return False

    # --- ETAPA 3: SISTEMA LIMBICO (Comandos de Controle) ---
    def _handle_system_commands(self, texto: str) -> bool:
        mapa = {
            "desligar": "sistema_desligar",
            "encerrar": "sistema_desligar",
            "dormir": "sistema_desligar",
            "status": "sistema_ping"
        }
        
        for gatilho, tool_name in mapa.items():
            if gatilho in texto:
                if tool_name == "sistema_desligar":
                    self._falar("Desligando protocolos. Até logo.")
                    bus.publicar(Evento(Eventos.SHUTDOWN, {}))
                    return True
                
                if registry:
                    res = registry.execute(tool_name)
                    self._falar(str(res))
                return True
        return False

    # --- ETAPA 4: FERRAMENTAS (Motor) ---
    def _handle_tools(self, texto: str) -> bool:
        """
        Lógica inteligente para detectar intenção de abrir apps.
        Suporta comandos explícitos ("abrir calc") e implícitos ("calculadora").
        """
        if not launcher: 
            self._falar("Launcher offline.")
            return True

        # 1. Tenta limpar verbos comuns para isolar o nome do App
        verbos = ["abrir", "iniciar", "tocar", "executar", "rodar", "bota", "põe", "lançar"]
        termo_busca = texto
        comando_explicito = False
        
        for v in verbos:
            if texto.startswith(v + " "):
                termo_busca = texto[len(v):].strip()
                comando_explicito = True
                break
        
        # 2. Busca no Launcher
        status, nome, caminho = launcher.buscar_candidato(termo_busca)
        
        if status == "EXATO":
            self._falar(f"Abrindo {nome}.")
            launcher.abrir_por_caminho(caminho)
            return True
            
        elif status == "SUGESTAO":
            self._falar(f"Encontrei '{nome}'. Deseja abrir?")
            self.contexto_pendente = {
                "tipo": "confirmar_app_learning",
                "dados": {"nome": nome, "caminho": caminho},
                "termo_original": termo_busca,
                "alvo_real": nome
            }
            return True
        
        # Se foi um comando EXPLICITO ("Abrir X") e não achou, avisa.
        if comando_explicito:
            self._falar(f"Não encontrei o aplicativo {termo_busca}.")
            return True

        # Se for comando de memória
        for gatilho in MEMORY_TRIGGERS:
            if gatilho in texto:
                if not llm: return False
                fato = texto.split(gatilho, 1)[1].strip()
                for c in ["que ", "sobre ", ":"]:
                    if fato.startswith(c): fato = fato[len(c):].strip()
                
                if fato:
                    llm.ensinar(fato)
                    self._falar("Memória gravada.")
                    return True

        return False

    # --- ETAPA 5: COGNIÇÃO SUPERIOR (LLM) ---
    def _handle_cognition(self, texto: str) -> bool:
        if not llm:
            self._falar("Minha conexão com o cérebro (LLM) está offline.")
            return True
        
        resposta = llm.pensar(texto)
        
        if curiosity:
            chance = 0.3
            is_short = len(resposta.split()) < 10
            if is_short or random.random() < chance:
                pergunta = curiosity.gerar_pergunta(texto)
                if pergunta:
                    resposta += f" ... A propósito, {pergunta}"
        
        self._falar(resposta)
        return True

    def _falar(self, texto: str):
        bus.publicar(Evento(Eventos.FALAR, {"texto": texto}))