import time
import re
import random
import json  # <--- IMPORTANTE: Necessário para entender o Cérebro
from typing import Optional, Tuple
from difflib import SequenceMatcher

# Imports do Sistema
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos

# --- DEPENDÊNCIAS ---
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
WAKE_WORDS = ["jarvis", "jarbas", "computer", "sexta-feira", "javis", "jardis"]
CONFIRMATION_YES = ["sim", "pode", "pode ser", "isso", "vai", "confirma", "abre", "ok", "claro", "positivo"]
CONFIRMATION_NO = ["não", "cancela", "errado", "esquece", "nada a ver", "negativo"]
MEMORY_TRIGGERS = ["memorize", "memoriza", "aprenda", "aprende", "grave", "lembre-se", "anote"]
ATTENTION_WINDOW = 40.0

class Orchestrator:
    def __init__(self):
        self.log = JarvisLogger("CORTEX_FRONTAL")
        
        # Inicia com a atenção ligada para aceitar comandos imediatos no boot/teste
        self._ultima_ativacao = time.time()
        self.contexto_pendente: Optional[dict] = None  
        
        # Inscreve para ouvir o evento de fala (Do Microfone)
        bus.inscrever(Eventos.FALA_RECONHECIDA, self.processar_input)
        self.log.info("🧠 Córtex Frontal Inicializado (Pipeline v3.6 - JSON Parser).")

    def start(self): pass
    def stop(self): pass

    # --- API GATEWAY ---
    def processar(self, texto: str) -> str:
        """Método síncrono para API/Testes."""
        if not texto: return ""
        
        # Mock do evento
        evento_mock = Evento(Eventos.FALA_RECONHECIDA, {"texto": texto})
        
        # Captura resposta
        resposta_final = []
        def interceptar_fala(evento):
            if evento.nome == Eventos.FALAR:
                resposta_final.append(evento.dados["texto"])

        bus.inscrever(Eventos.FALAR, interceptar_fala)
        self.processar_input(evento_mock)
        return " | ".join(resposta_final) if resposta_final else "Sem resposta vocal."

    def processar_input(self, evento: Evento):
        """Pipeline Principal."""
        try:
            texto_bruto = evento.dados.get("texto", "")
            if not texto_bruto: return

            # 1. Normalização
            comando_limpo = re.sub(r'[^\w\s]', '', texto_bruto.lower()).strip()
            comando_limpo = re.sub(r'(.)\1{2,}', r'\1', comando_limpo)
            
            # 2. Pipeline de Decisão
            if self._handle_confirmation(comando_limpo): return
            
            is_wake, texto_payload = self._check_attention(comando_limpo)
            if not is_wake: return 

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
            self._falar("Ocorreu um erro interno.")

    # --- ETAPA 1: ATENÇÃO ---
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
                    sucesso = reflexos.adicionar_correcao(erro, correcao)
                    msg = f"Entendido. '{erro}' agora é '{correcao}'." if sucesso else "Erro ao gravar reflexo."
                    self._falar(msg)
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
                reflexos.adicionar_correcao(dados['termo_original'].split()[0], dados['alvo_real'].lower())
        self.contexto_pendente = None
        self._ultima_ativacao = time.time()

    # --- ETAPA 3: SISTEMA LIMBICO ---
    def _handle_system_commands(self, texto: str) -> bool:
        if texto == "volume":
            self._falar("Volume atual: Ajustando para mostrar painel.")
            if registry: registry.execute("sistema", comando="aumenta o volume")
            return True

        mapa = {"desligar": "sistema_desligar", "status": "sistema_status"}
        for gatilho, tool_name in mapa.items():
            if gatilho in texto:
                if tool_name == "sistema_desligar":
                    self._falar("Desligando protocolos.")
                    bus.publicar(Evento(Eventos.SHUTDOWN, {}))
                    return True
                if tool_name == "sistema_status":
                    self._falar("Sistemas operacionais e auditivos: 100% online.")
                    return True
        return False

    # --- ETAPA 4: FERRAMENTAS ---
    def _handle_tools(self, texto: str) -> bool:
        if not launcher: 
            self.log.warning("Launcher está None.")

        # 1. LAUNCHER
        verbos_abrir = ["abrir", "iniciar", "executar", "rodar", "lançar"]
        for v in verbos_abrir:
            if texto.startswith(v + " ") or texto == v: # Aceita comando exato "abrir"
                termo_busca = texto[len(v):].strip()
                
                if not termo_busca:
                    self._falar("Por favor, diga o nome do programa que deseja abrir.")
                    return True 

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
                    
                    self._falar(f"Não encontrei o aplicativo '{termo_busca}'.")
                    return True
                break 

        if registry:
            # 2. MÚSICA
            verbos_musica = [
                "tocar ", "toca ", "ouvir ", "bota ", "põe ", "toka ", "escute ", "reproduzir ",
                "proxima", "próxima", "anterior", "voltar", "pular", "avançar",
                "pausar", "continuar", "parar", "play", "pause"
            ]
            
            # Tratamento de comandos curtos
            if texto in ["tocar", "toca", "play"]:
                self._falar("Continuando a música.")
                registry.execute("spotify", comando="play")
                return True

            if any(texto.startswith(p) for p in verbos_musica):
                self.log.info("🎵 Intenção de música detectada.")
                resultado = registry.execute("spotify", comando=texto)
                resp_str = str(resultado).lower()
                
                # Fallback se Spotify estiver fechado
                erros_comuns = ["offline", "sem internet", "fechado", "não está rodando", "erro"]
                if any(err in resp_str for err in erros_comuns) and launcher:
                    self.log.info("⚠️ Agente falhou/offline. Acionando Fallback Launcher.")
                    self._falar("O Spotify parece fechado. Vou abri-lo.")
                    status, nome, caminho = launcher.buscar_candidato("spotify")
                    if caminho:
                        launcher.abrir_por_caminho(caminho)
                    else:
                        self._falar("Não encontrei o aplicativo instalado.")
                    return True
                
                self._falar(str(resultado))
                return True

            # 3. NOMINAL
            nome_agente = registry.identificar_agente(texto)
            if nome_agente:
                self.log.info(f"🕵️ Agente nominal acionado: {nome_agente}")
                self._falar(str(registry.execute(nome_agente, comando=texto)))
                return True

        # 4. LAUNCHER (SEM VERBO)
        if launcher:
            status, nome, caminho = launcher.buscar_candidato(texto)
            if status == "EXATO":
                self._falar(f"Abrindo {nome}.")
                launcher.abrir_por_caminho(caminho)
                return True

        # 5. MEMÓRIA (REGEX)
        for gatilho in MEMORY_TRIGGERS:
            if gatilho in texto and "aprenda que" not in texto:
                payload = texto.split(gatilho, 1)[1].strip()
                if not payload:
                    self._falar("O que você gostaria que eu memorizasse?")
                    return True
                if not llm: return False
                llm.ensinar(payload)
                self._falar("Memória gravada.")
                return True

        return False

    # --- ETAPA 5: COGNIÇÃO SUPERIOR (COM JSON PARSER) ---
    def _handle_cognition(self, texto: str) -> bool:
        if not llm:
            self._falar("Estou sem conexão com meu cérebro.")
            return True
        
        # 1. Pensa (Pode vir texto ou JSON)
        resposta_bruta = llm.pensar(texto)
        
        # 2. Tenta extrair e executar JSON
        try:
            if "{" in resposta_bruta and "}" in resposta_bruta:
                # Regex para encontrar o primeiro objeto JSON válido (ignora lixo antes/depois)
                match = re.search(r'\{.*\}', resposta_bruta, re.DOTALL)
                if match:
                    json_str = match.group(0)
                    acao = json.loads(json_str)
                    
                    ferramenta = acao.get("ferramenta")
                    
                    # Ação: Memória
                    if ferramenta == "memoria_gravar":
                        dado = acao.get("dado") or acao.get("parametro")
                        if dado:
                            llm.ensinar(dado)
                            self._falar(f"Entendido. Memorizei: {dado}")
                        return True
                    
                    # Ação: Sistema (ex: "abrir navegador")
                    if ferramenta == "sistema":
                        cmd = acao.get("comando", "")
                        # Recicla a lógica de ferramentas passando o comando extraído
                        return self._handle_tools(cmd)

                    # Ação: Spotify (via JSON)
                    if ferramenta == "spotify":
                        cmd = acao.get("comando", "")
                        return self._handle_tools(cmd)

        except Exception as e:
            self.log.warning(f"Falha ao parsear JSON do LLM: {e}")

        # 3. Tratamento de Alucinações
        if "sistema_ping" in resposta_bruta or "status" in resposta_bruta:
             self._falar("Todos os sistemas operacionais.")
             return True

        # 4. Resposta Chat
        if curiosity:
            chance = 0.3
            if len(resposta_bruta.split()) < 10 or random.random() < chance:
                pergunta = curiosity.gerar_pergunta(texto)
                if pergunta: resposta_bruta += f" ... {pergunta}"
        
        self._falar(resposta_bruta)
        return True

    def _falar(self, texto: str):
        bus.publicar(Evento(Eventos.FALAR, {"texto": texto}))