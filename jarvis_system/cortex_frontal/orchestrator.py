import time
import re
import random
from typing import Optional, Tuple
from difflib import SequenceMatcher

# Imports do Sistema
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos

# --- DEPENDÊNCIAS ---
# Removemos o try/except genérico para expor erros reais de importação se houverem,
# mas mantemos verificações de segurança no código.
try:
    from jarvis_system.cortex_motor.tool_registry import registry
    from jarvis_system.cortex_motor.launcher import launcher 
    from jarvis_system.cortex_frontal.brain_llm import llm 
    from jarvis_system.cortex_frontal.subconsciente import curiosity
    from jarvis_system.hipocampo.reflexos import reflexos
except ImportError as e:
    print(f"CRITICAL: Erro de importação no Córtex Frontal: {e}")
    registry, launcher, llm, curiosity, reflexos = None, None, None, None, None

# --- CONFIGURAÇÃO COGNITIVA ---
WAKE_WORDS = ["jarvis", "jarbas", "computer", "sexta-feira"]
CONFIRMATION_YES = ["sim", "pode", "pode ser", "isso", "vai", "confirma", "abre", "ok", "claro", "positivo"]
CONFIRMATION_NO = ["não", "cancela", "errado", "esquece", "nada a ver", "negativo"]
MEMORY_TRIGGERS = ["memorize", "memoriza", "aprenda", "aprende", "grave", "lembre-se", "anote"]
ATTENTION_WINDOW = 40.0

class Orchestrator:
    def __init__(self):
        self.log = JarvisLogger("CORTEX_FRONTAL")
        self._ultima_ativacao = 0.0
        self.contexto_pendente: Optional[dict] = None  
        
        bus.inscrever(Eventos.FALA_RECONHECIDA, self.processar_input)
        self.log.info("🧠 Córtex Frontal Inicializado (Pipeline v2.8 - Fallback Spotify).")

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

            self._ultima_ativacao = time.time()
            self.log.info(f"🤔 Processando: '{texto_payload}'")

            # Pipeline de Ações
            if self._handle_learning(texto_payload): return
            if self._handle_system_commands(texto_payload): return
            if self._handle_tools(texto_payload): return
            if self._handle_cognition(texto_payload): return

        except Exception as e:
            self.log.error(f"Erro no processamento cognitivo: {e}")
            self._falar("Ocorreu um erro interno nos meus circuitos.")

    # --- ETAPA 1: ATENÇÃO & WAKE WORD (FUZZY) ---
    def _check_attention(self, texto: str) -> Tuple[bool, str]:
        tempo_passado = time.time() - self._ultima_ativacao
        
        def is_similar(a, b, threshold=0.8):
            return SequenceMatcher(None, a, b).ratio() >= threshold

        if tempo_passado < ATTENTION_WINDOW:
            palavras = texto.split()
            for i, palavra in enumerate(palavras):
                for w in WAKE_WORDS:
                    if is_similar(palavra, w):
                        payload = " ".join(palavras[:i] + palavras[i+1:])
                        return True, payload
            return True, texto

        if not texto: return False, ""
        primeira_palavra = texto.split()[0]
        
        for w in WAKE_WORDS:
            if is_similar(primeira_palavra, w):
                payload = texto[len(primeira_palavra):].strip()
                return True, payload
            if f" {w} " in f" {texto} ":
                parts = texto.split(w, 1)
                if len(parts[0]) < 10: 
                    return True, parts[1].strip()
        return False, ""

    # --- ETAPA 1.5: LEARNING ---
    def _handle_learning(self, texto: str) -> bool:
        padroes = [
            r"aprenda que (.+) significa (.+)",
            r"aprenda que (.+) quer dizer (.+)",
            r"entenda (.+) como (.+)"
        ]
        for padrao in padroes:
            match = re.search(padrao, texto)
            if match:
                erro, correcao = match.group(1).strip(), match.group(2).strip()
                if reflexos:
                    self._falar(reflexos.aprender(erro, correcao))
                else:
                    self._falar("Memória offline.")
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
                reflexos.aprender(dados['termo_original'].split()[0], dados['alvo_real'].lower())
        self.contexto_pendente = None
        self._ultima_ativacao = time.time()

    # --- ETAPA 3: SISTEMA LIMBICO ---
    def _handle_system_commands(self, texto: str) -> bool:
        mapa = {"desligar": "sistema_desligar", "status": "sistema_ping"}
        for gatilho, tool_name in mapa.items():
            if gatilho in texto:
                if tool_name == "sistema_desligar":
                    self._falar("Desligando protocolos.")
                    bus.publicar(Evento(Eventos.SHUTDOWN, {}))
                    return True
                if registry:
                    self._falar(str(registry.execute(tool_name)))
                return True
        return False

    # --- ETAPA 4: FERRAMENTAS (COM FALLBACK PARA SPOTIFY) ---
    def _handle_tools(self, texto: str) -> bool:
        # Se launcher for None aqui, o import falhou lá em cima.
        if not launcher: 
            self.log.warning("Launcher está None. Verifique imports.")

        if registry:
            # 1. Verifica Agente Nominal
            nome_agente = registry.identificar_agente(texto)
            if nome_agente:
                self.log.info(f"🕵️ Agente acionado: {nome_agente}")
                self._falar(str(registry.execute(nome_agente, comando=texto)))
                return True

            # 2. Lógica Especializada para Música (Spotify)
            if texto.startswith("tocar ") or texto.startswith("toca "):
                self.log.info("🎵 Verbo de música detectado. Tentando Agente Spotify...")
                
                # A) Tenta executar via Agente Especialista
                resultado = registry.execute("spotify", comando=texto)
                resp_str = str(resultado).lower()
                
                # B) Lógica de Fallback: Se o agente reclamar, usamos a força bruta (Launcher)
                # Palavras chaves de erro comuns: "offline", "fechado", "erro", "não encontrei"
                erros_comuns = ["offline", "sem internet", "fechado", "não está rodando", "erro"]
                
                if any(err in resp_str for err in erros_comuns) and launcher:
                    self.log.info("⚠️ Agente falhou/offline. Acionando Fallback Launcher.")
                    self._falar("O Spotify parece fechado. Vou abri-lo para você.")
                    
                    # Tenta abrir o aplicativo diretamente
                    status, nome, caminho = launcher.buscar_candidato("spotify")
                    if caminho:
                        launcher.abrir_por_caminho(caminho)
                        return True
                    else:
                        self._falar("E não encontrei o aplicativo instalado.")
                        return True
                
                # Se deu tudo certo ou o erro não é recuperável
                self._falar(str(resultado))
                return True

        # 3. Comandos de Sistema Operacional (Launcher Genérico)
        verbos = ["abrir", "iniciar", "executar", "rodar", "bota", "põe", "lançar"]
        termo_busca = texto
        comando_explicito = False
        
        for v in verbos:
            if texto.startswith(v + " "):
                termo_busca = texto[len(v):].strip()
                comando_explicito = True
                break
        
        if launcher:
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
        else:
            if comando_explicito:
                self._falar("Meu módulo lançador está offline.")
                return True

        # Memória Rápida
        for gatilho in MEMORY_TRIGGERS:
            if gatilho in texto and "aprenda que" not in texto:
                if not llm: return False
                llm.ensinar(texto.split(gatilho, 1)[1].strip())
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