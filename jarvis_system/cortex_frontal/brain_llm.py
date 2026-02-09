import os
import time
import datetime
import re
import random
from typing import Optional, List
from groq import Groq, RateLimitError, APIConnectionError
import ollama
from dotenv import load_dotenv

# --- CARREGA O .ENV EXPLICITAMENTE ---
load_dotenv()

# Imports do Sistema
from jarvis_system.cortex_frontal.observability import JarvisLogger
# Importa o banco de frases
from jarvis_system.area_broca.frases_padrao import obter_frase, FRASES_DO_SISTEMA

log = JarvisLogger("CORTEX_BRAIN")

try:
    from jarvis_system.hipocampo.memoria import memoria
except ImportError:
    log.warning("Hipocampo (Memória) não encontrado ou falhou ao carregar.")
    memoria = None

class KeyManager:
    """Gerenciador de Rotação de Chaves para evitar Rate Limit"""
    def __init__(self):
        self.keys = []
        self._load_keys()
        self.current_index = 0

    def _load_keys(self):
        # 1. Pega a chave principal
        main_key = os.getenv("GROQ_API_KEY")
        if main_key:
            self.keys.append(main_key)
        
        # 2. Pega as chaves numeradas
        for i in range(1, 20):
            k = os.getenv(f"GROQ_API_KEY_{i}")
            if k:
                self.keys.append(k)
        
        # Embaralha para distribuir a carga
        if self.keys:
            random.shuffle(self.keys)
            log.info(f"🔑 KeyManager: {len(self.keys)} chaves Groq carregadas no pool.")
        else:
            log.critical("❌ Nenhuma chave GROQ_API_KEY encontrada no .env!")

    def get_current_client(self) -> Optional[Groq]:
        if not self.keys: return None
        return Groq(api_key=self.keys[self.current_index])

    def rotate(self):
        """Avança para a próxima chave da lista"""
        if not self.keys: return
        anterior = self.current_index
        self.current_index = (self.current_index + 1) % len(self.keys)
        log.warning(f"🔄 Rotacionando API Key: ID {anterior} -> ID {self.current_index}")

class HybridBrain:
    def __init__(self):
        self.key_manager = KeyManager()
        self.client_groq = self.key_manager.get_current_client()
        
        self.model_cloud = os.getenv("JARVIS_MODEL_CLOUD", "llama-3.3-70b-versatile")
        self.model_local = os.getenv("JARVIS_MODEL_LOCAL", "qwen2:0.5b")
        
        # Lista de categorias para o Prompt saber o que existe
        self.categorias_str = ", ".join(FRASES_DO_SISTEMA.keys())

        if self.client_groq:
            log.info(f"☁️ Córtex Nuvem Conectado: {self.model_cloud}")
        else:
            log.warning("⚠️ Modo Offline Forçado (Sem API Keys).")

    @property
    def _dynamic_system_prompt(self) -> str:
        now = datetime.datetime.now()
        data_str = now.strftime("%d/%m/%Y")
        hora_str = now.strftime("%H:%M")
        
        return (
            f"Você é J.A.R.V.I.S., uma IA avançada de automação e companhia. Data: {data_str}, Hora: {hora_str}.\n\n"
            "### DIRETRIZES MESTRAS:\n"
            "1. **AUTOMACAO**: Se o usuário pedir música, abrir apps ou controle de PC, retorne APENAS um JSON.\n"
            "   - Música: `{\"ferramenta\": \"spotify\", \"comando\": \"...\"}`\n"
            "   - App: `{\"ferramenta\": \"sistema\", \"comando\": \"abrir ...\"}`\n\n"
            "2. **MEMÓRIA**: Se o usuário disser 'Aprenda que...', retorne JSON: `{\"ferramenta\": \"memoria_gravar\", \"dado\": \"...\"}`\n\n"
            
            # DIRETRIZ DE VOZ PRONTA (Economia + Qualidade)
            "3. **VOZ PRE-GRAVADA** (PRIORIDADE MÁXIMA):\n"
            f"   Se a resposta se encaixar perfeitamente em uma destas categorias: [{self.categorias_str}], "
            "NÃO escreva texto. Responda APENAS com a tag da categoria.\n"
            "   Exemplos:\n"
            "   - 'Jarvis, status.' -> `[[STATUS]]`\n"
            "   - 'Obrigado.' -> `[[CONFIRMACAO]]`\n"
            "   - 'Bom dia.' -> `[[BOAS_VINDAS]]`\n\n"
            
            # DIRETRIZ DE EMOÇÃO PARA VOZ NOVA (Fish Audio)
            "4. **VOZ GERADA (CHAT)**:\n"
            "   Ao gerar texto novo, você DEVE escolher a emoção correta para a síntese de voz.\n"
            "   Use APENAS UMA tag no início da frase (dentro de parênteses).\n"
            "   \n"
            "   **Lista de Emoções Disponíveis:**\n"
            "   - Positivas: (friendly), (excited), (satisfied), (delighted), (joyful), (proud), (grateful), (confident), (amused)\n"
            "   - Negativas: (angry), (sad), (disdainful), (scared), (worried), (impatient), (nervous), (disgusted), (serious)\n"
            "   - Especiais: (whispering), (shouting), (sarcastic), (painful), (sincere)\n"
            "   - Sons: (laughing), (chuckling), (sighing), (sobbing)\n"
            "   \n"
            "   **Exemplos de Uso:**\n"
            "   - `(friendly) Olá senhor, como posso ajudar?`\n"
            "   - `(excited) Compilei o código com sucesso!`\n"
            "   - `(serious) Detectei uma intrusão no servidor.`\n"
            "   - `(whispering) Fale baixo, alguém pode ouvir.`\n"
            "   - `(sarcastic) Ah claro, uma ideia brilhante...`\n"
            "   - `(laughing) Ha ha ha, essa foi boa senhor.`\n\n"

            "5. **CHAT GERAL**: Se não for automação nem frase pronta, RESPONDA COMO CHATBOT.\n"
            "   - Seja espirituoso, breve e útil. Personalidade: Jarvis do Homem de Ferro.\n"
            "   - Respostas curtas são melhores para síntese de voz.\n\n"
            
            "### REGRAS ESPECÍFICAS:\n"
            "- Se o usuário falar apenas 'status', assuma que é um check de sistema.\n"
            "- Não invente nomes de ferramentas."
        )

    def _verificar_intencao_forcada(self, texto: str) -> Optional[str]:
        """Heurística para interceptar comandos óbvios de música."""
        t = texto.lower().strip()
        verbos_busca = ["tocar", "ouvir", "bota", "reproduzir", "som de", "escutar"]
        for verbo in verbos_busca:
            if re.search(rf"\b{verbo}\s+.{{2,}}", t):
                return f"Comando de música detectado: '{texto}'. Ação esperada: spotify"
        return None

    def pensar(self, texto_usuario: str) -> str:
        start_time = time.time()
        
        # 1. RAG
        contexto_rag = self._recuperar_memoria(texto_usuario)
        
        # 2. Reforço
        dica_intencao = self._verificar_intencao_forcada(texto_usuario)
        
        # 3. Prompt
        prompt_final = self._montar_prompt_usuario(texto_usuario, contexto_rag, dica_intencao)
        
        resposta = ""
        provider = "NENHUM"

        # 4. Inferência (Groq com Rotação)
        if self.client_groq:
            tentativas = 3
            for i in range(tentativas):
                try:
                    resposta = self._inferencia_nuvem(prompt_final)
                    provider = f"NUVEM ({self.model_cloud})"
                    break 
                except (RateLimitError, APIConnectionError) as e:
                    log.warning(f"⚠️ Erro na Groq (Tentativa {i+1}/{tentativas}): {e}")
                    self.key_manager.rotate()
                    self.client_groq = self.key_manager.get_current_client()
                    time.sleep(0.5)
                except Exception as e:
                    log.error(f"❌ Erro genérico na nuvem: {e}")
                    break 
        
        # 5. Fallback Local
        if not resposta:
            try:
                log.info("🔻 Caindo para modelo LOCAL...")
                resposta = self._inferencia_local(prompt_final)
                provider = f"LOCAL ({self.model_local})"
            except Exception as e:
                log.critical(f"💀 Falha Cognitiva Total: {e}")
                return "Senhor, meus sistemas neurais falharam completamente."

        # 6. INTERCEPTAÇÃO DE FRASES PRONTAS
        # Verifica se o LLM mandou uma tag do tipo [[CATEGORIA]]
        if resposta.startswith("[[") and resposta.endswith("]]"):
            categoria_detectada = resposta
            frase_pronta = obter_frase(categoria_detectada)
            
            if frase_pronta:
                log.info(f"🎯 LLM escolheu tag '{categoria_detectada}'. Substituindo por áudio Pro: '{frase_pronta[:20]}...'")
                resposta = frase_pronta
            else:
                # Se o LLM alucinou uma categoria que não existe, remove os colchetes e fala o texto
                resposta = categoria_detectada.replace("[[", "").replace("]]", "")

        latency = time.time() - start_time
        log.info(f"🧠 Pensamento: {latency:.2f}s via {provider}")
        return resposta

    def ensinar(self, fato: str):
        """Método direto para gravar memória"""
        if not memoria: return "Erro: Memória off."
        try:
            if hasattr(memoria, "adicionar_memoria"): memoria.adicionar_memoria(fato)
            elif hasattr(memoria, "memorizar"): memoria.memorizar(fato)
            elif hasattr(memoria, "gravar"): memoria.gravar(fato)
            else: return "Erro técnico na memória."
            return "Memória gravada com sucesso."
        except Exception as e:
            log.error(f"Erro ao gravar memória: {e}")
            return "Falha ao acessar banco de memória."

    # --- AUXILIARES ---

    def _recuperar_memoria(self, query: str) -> str:
        if not memoria: return ""
        try:
            dados = memoria.relembrar(query)
            if dados: return dados
        except: pass
        return ""

    def _montar_prompt_usuario(self, query: str, context: str, dica: str = None) -> str:
        reforco = ""
        if dica:
            reforco = f"INSTRUÇÃO DO SISTEMA: {dica}. OBEDEÇA A ESTA CLASSIFICAÇÃO.\n"

        base = f"USUÁRIO: {query}"
        ctx = f"MEMÓRIA/CONTEXTO:\n{context}\n" if context else ""
        
        return f"{reforco}{ctx}---\n{base}"

    def _inferencia_nuvem(self, prompt: str) -> str:
        if not self.client_groq: raise Exception("Groq Off")
        chat = self.client_groq.chat.completions.create(
            model=self.model_cloud,
            messages=[
                {"role": "system", "content": self._dynamic_system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4, # Baixa temperatura ajuda a acertar as tags [[TAG]]
            max_tokens=300,
            timeout=6.0
        )
        return chat.choices[0].message.content.strip()

    def _inferencia_local(self, prompt: str) -> str:
        response = ollama.chat(
            model=self.model_local,
            messages=[
                {"role": "system", "content": self._dynamic_system_prompt},
                {"role": "user", "content": prompt}
            ],
            options={"temperature": 0.4, "num_predict": 128}
        )
        return response['message']['content'].strip()

try:
    llm = HybridBrain()
except Exception as e:
    log.critical(f"FATAL: {e}")
    llm = None