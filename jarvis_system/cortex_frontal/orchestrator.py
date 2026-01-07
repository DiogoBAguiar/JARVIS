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
ATTENTION_WINDOW = 40.0  # Janela de atenção estendida

class Orchestrator:
    def __init__(self):
        self.log = JarvisLogger("CORTEX_FRONTAL")
        self._ultima_ativacao = 0.0
        self.contexto_pendente: Optional[dict] = None  
        
        bus.inscrever(Eventos.FALA_RECONHECIDA, self.processar_input)
        self.log.info("🧠 Córtex Frontal Inicializado (Pipeline v2.7 - Active Learning).")

    def start(self): pass
    def stop(self): pass

    def processar_input(self, evento: Evento):
        try:
            texto_bruto = evento.dados.get("texto", "")
            if not texto_bruto: return

            # 1. Normalização
            comando_limpo = re.sub(r'[^\w\s]', '', texto_bruto.lower()).strip()
            
            # 2. Pipeline de Decisão
            if self._handle_confirmation(comando_limpo): return
            
            is_wake, texto_payload = self._check_attention(comando_limpo)
            if not is_wake: return 

            # --- RESPOSTA AO CHAMADO ---
            if not texto_payload:
                saudacoes = ["Pois não?", "Estou aqui.", "Sim?", "Às ordens."]
                self._falar(random.choice(saudacoes))
                self._ultima_ativacao = time.time()
                return

            # Atualiza "foco"
            self._ultima_ativacao = time.time()
            self.log.info(f"🤔 Processando: '{texto_payload}'")

            # --- NOVO: Verifica Aprendizado Ativo ---
            if self._handle_learning(texto_payload): return

            if self._handle_system_commands(texto_payload): return
            if self._handle_tools(texto_payload): return
            if self._handle_cognition(texto_payload): return

        except Exception as e:
            self.log.error(f"Erro no processamento cognitivo: {e}")
            self._falar("Ocorreu um erro interno nos meus circuitos.")

    # --- ETAPA 1: ATENÇÃO & WAKE WORD ---
    def _check_attention(self, texto: str) -> Tuple[bool, str]:
        tempo_passado = time.time() - self._ultima_ativacao
        if tempo_passado < ATTENTION_WINDOW:
            for w in WAKE_WORDS:
                if w in texto:
                    return True, texto.replace(w, "").strip()
            return True, texto

        for w in WAKE_WORDS:
            if texto.startswith(w):
                payload = texto[len(w):].strip()
                return True, payload
            
            if f" {w} " in f" {texto} ":
                parts = texto.split(w, 1)
                prefixo = parts[0]
                if len(prefixo) < 6:
                    payload = parts[1].strip()
                    return True, payload

        return False, ""

    # --- ETAPA 1.5: APRENDIZADO ATIVO (Active Learning) ---
    def _handle_learning(self, texto: str) -> bool:
        """
        Ensina o sistema a corrigir erros fonéticos em tempo real.
        Ex: "Aprenda que tocasho significa tocar"
        """
        padroes = [
            r"aprenda que (.+) significa (.+)",
            r"aprenda que (.+) quer dizer (.+)",
            r"aprenda que (.+) é igual a (.+)",
            r"entenda (.+) como (.+)"
        ]

        for padrao in padroes:
            match = re.search(padrao, texto)
            if match:
                erro = match.group(1).strip()
                correcao = match.group(2).strip()
                
                if reflexos:
                    msg = reflexos.aprender(erro, correcao)
                    self._falar(msg)
                else:
                    self._falar("Meu sistema de memória (Reflexos) está offline.")
                
                return True
        return False

    # --- ETAPA 2: REFLEXO ---
    def _handle_confirmation(self, texto: str) -> bool:
        if not self.contexto_pendente: return False

        if any(w in texto.split() for w in CONFIRMATION_YES):
            self._executar_pendente()
            return True
        elif any(w in texto.split() for w in CONFIRMATION_NO):
            self._falar("Cancelado.")
            self.contexto_pendente = None
            self._ultima_ativacao = time.time()
            return True
        return False

    def _executar_pendente(self):
        cmd_type = self.contexto_pendente.get("tipo")
        dados = self.contexto_pendente
        
        if cmd_type == "confirmar_app_learning":
            app_info = dados.get("dados", {})
            self._falar(f"Entendido. Abrindo {dados['alvo_real']} e aprendendo.")
            
            if launcher: launcher.abrir_por_caminho(app_info.get('caminho'))
            
            if reflexos:
                termo_erro = dados['termo_original'].split()[0]
                nome_app = dados['alvo_real'].lower()
                reflexos.aprender(termo_erro, nome_app)
        
        self.contexto_pendente = None
        self._ultima_ativacao = time.time()

    # --- ETAPA 3: SISTEMA LIMBICO ---
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
                    self._falar("Desligando protocolos.")
                    bus.publicar(Evento(Eventos.SHUTDOWN, {}))
                    return True
                if registry:
                    res = registry.execute(tool_name)
                    self._falar(str(res))
                return True
        return False

    # --- ETAPA 4: FERRAMENTAS ---
    def _handle_tools(self, texto: str) -> bool:
        if not launcher: 
            self._falar("Launcher offline.")
            return True

        if registry:
            nome_agente = registry.identificar_agente(texto)
            if nome_agente:
                self.log.info(f"🕵️ Agente acionado: {nome_agente}")
                resultado = registry.execute(nome_agente, comando=texto)
                self._falar(str(resultado))
                return True

        verbos = ["abrir", "iniciar", "tocar", "executar", "rodar", "bota", "põe", "lançar"]
        termo_busca = texto
        comando_explicito = False
        
        for v in verbos:
            if texto.startswith(v + " "):
                termo_busca = texto[len(v):].strip()
                comando_explicito = True
                break
        
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
        
        if comando_explicito:
            self._falar(f"Não encontrei o aplicativo {termo_busca}.")
            return True

        for gatilho in MEMORY_TRIGGERS:
            # Nota: "aprenda que" é capturado antes pelo _handle_learning. 
            # Isso aqui captura "memorize que hoje é dia 5".
            if gatilho in texto and "aprenda que" not in texto:
                if not llm: return False
                fato = texto.split(gatilho, 1)[1].strip()
                llm.ensinar(fato)
                self._falar("Memória gravada.")
                return True

        return False

    # --- ETAPA 5: COGNIÇÃO SUPERIOR ---
    def _handle_cognition(self, texto: str) -> bool:
        if not llm:
            self._falar("Estou sem conexão com meu cérebro.")
            return True
        
        resposta = llm.pensar(texto)
        
        if curiosity:
            chance = 0.3
            if len(resposta.split()) < 10 or random.random() < chance:
                pergunta = curiosity.gerar_pergunta(texto)
                if pergunta: resposta += f" ... {pergunta}"
        
        self._falar(resposta)
        return True

    def _falar(self, texto: str):
        bus.publicar(Evento(Eventos.FALAR, {"texto": texto}))