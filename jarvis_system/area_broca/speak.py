import os
import threading
import queue
import json
import pygame
import pyttsx3
import requests
import re
import time
from datetime import datetime
from dotenv import load_dotenv

# Core Imports
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos

try:
    from jarvis_system.cortex_frontal.voice_director import VoiceDirector
except ImportError:
    VoiceDirector = None

load_dotenv()

FISH_AUDIO_API_URL = "https://api.fish.audio/v1/tts"

# --- MAPA DE EMOÇÕES (JARVIS -> FISH AUDIO) ---
# Mapeia a intenção do sistema para as tags oficiais da documentação da API
FISH_TAGS = {
    # Contextos de Sistema (Sub-contextos)
    "boot": "(confident)",      # "Jarvis Online" -> Confiança
    "return": "(happy)",        # "Bem vindo de volta" -> Felicidade/Amigável
    "query": "(curious)",       # "Deseja algo?" -> Curiosidade/Interesse
    "status": "(serious)",      # "Bateria 10%" -> Seriedade/Profissional
    "passive": "(relaxed)",     # "À disposição" -> Relaxado
    "alert": "(worried)",       # "Erro detectado" -> Preocupação
    
    # Categorias Específicas (Sobrescrevem contexto)
    "HUMOR": "(amused)",        # Piadas -> Divertido
    "COMBATE": "(shouting)",    # Combate -> Gritando/Tenso
    "FILOSOFIA": "(thoughtful)" # Reflexão -> Pensativo
}

class NeuralSpeaker:
    def __init__(self):
        self.log = JarvisLogger("BROCA_VOICE")
        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread = None
        
        self.fish_api_key = os.getenv("FISHAUDIO_API_KEY")
        self.fish_model_id = os.getenv("FISHAUDIO_MODEL_ID")

        # --- SISTEMAS COGNITIVOS ---
        self.voice_director = VoiceDirector() if VoiceDirector else None

        # --- DIRETÓRIOS ---
        self.base_dir = os.path.join(os.getcwd(), "jarvis_system", "data", "voices")
        self.audio_dir = os.path.join(self.base_dir, "assets")
        self.index_path = os.path.join(self.base_dir, "voice_index.json")
        
        os.makedirs(self.audio_dir, exist_ok=True)

        self.voice_index = {} 
        self._carregar_indice()

        # --- INICIALIZAÇÃO DE ÁUDIO (BUFFER OTIMIZADO) ---
        self._inicializar_driver_audio()
            
        try: self.engine_offline = pyttsx3.init()
        except: self.engine_offline = None
        
        # Inscreve no Barramento de Eventos
        bus.inscrever(Eventos.FALAR, self._adicionar_a_fila)
        self.log.info("🗣️ Área de Broca (NeuralSpeaker v2.6) Online - Emotion Engine Fixed.")

    def _inicializar_driver_audio(self):
        """
        Inicializa o mixer com um buffer maior (4096) para evitar
        que o áudio seja cortado no início (underrun).
        """
        try:
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=4096)
            pygame.mixer.init()
        except Exception as e:
            self.log.warning(f"Pygame Mixer High-Buffer falhou, usando padrão: {e}")
            try: pygame.mixer.init()
            except: pass

    def _normalizar_chave(self, texto: str) -> str:
        """
        Cria uma hash agressiva (apenas letras e números) para maximizar Cache Hit.
        Ignora tags de emoção ex: (happy)
        """
        if not texto: return ""
        # Remove tags de emoção e conteúdo entre parênteses
        texto = re.sub(r'\([^)]*\)', '', texto) 
        texto = texto.lower()
        # Remove acentos e caracteres especiais
        trans = str.maketrans("áàãâéêíóõôúç", "aaaaeeiooouc")
        texto = texto.translate(trans)
        # Mantém APENAS letras e números
        return re.sub(r'[^a-z0-9]', '', texto)

    def _carregar_indice(self):
        """Carrega o mapa mental de vozes existentes."""
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item_id, metadata in data.items():
                        chave = metadata.get("key_hash")
                        if chave:
                            self.voice_index[chave] = metadata
                self.log.info(f"📂 Índice Vocal Carregado: {len(self.voice_index)} memórias auditivas.")
            except Exception as e:
                self.log.error(f"Erro ao ler voice_index.json: {e}")
                self.voice_index = {}
        else:
            self.log.warning("⚠️ voice_index.json não encontrado. Criando novo índice em breve.")

    def _salvar_indice(self, novo_dado: dict):
        """Persiste a nova memória auditiva no JSON."""
        dados_atuais = {}
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    dados_atuais = json.load(f)
            except: pass
        
        item_id = novo_dado["id"]
        dados_atuais[item_id] = novo_dado
        
        try:
            with open(self.index_path, 'w', encoding='utf-8') as f:
                json.dump(dados_atuais, f, indent=4, ensure_ascii=False)
            self.voice_index[novo_dado["key_hash"]] = novo_dado
        except Exception as e:
            self.log.error(f"Falha ao salvar índice: {e}")

    def _determinar_categoria(self, texto_limpo: str) -> str:
        """Categoriza a frase baseada em padrões ou memória."""
        chave = self._normalizar_chave(texto_limpo)
        
        if chave in self.voice_index:
            return self.voice_index[chave].get("category", "GENERICO")
            
        t = texto_limpo.lower()
        if "erro" in t or "falha" in t or "alerta" in t or "perigo" in t: return "ALERTA"
        if "bom dia" in t or "boa tarde" in t or "boa noite" in t or "bem-vindo" in t: return "BOAS_VINDAS"
        if "online" in t or "iniciando" in t: return "BOAS_VINDAS"
        if "status" in t or "operacional" in t: return "STATUS"
        
        return "GENERICO"

    def _detectar_temporal(self, texto: str) -> str:
        t = texto.lower()
        if "bom dia" in t: return "morning"
        if "boa tarde" in t: return "afternoon"
        if "boa noite" in t: return "night"
        
        hora = datetime.now().hour
        if 5 <= hora < 12: return "morning"
        elif 12 <= hora < 18: return "afternoon"
        else: return "night"

    def _detectar_sub_contexto(self, texto: str, categoria: str) -> str:
        t = texto.lower()
        if categoria == "ALERTA" or categoria == "ERRO_SISTEMA": return "alert"
        if categoria == "BOAS_VINDAS":
            if "online" in t or "iniciando" in t: return "boot"
            if "volta" in t or "retomada" in t: return "return"
            if "?" in t: return "query"
            return "passive"
        if "?" in t: return "query"
        if "status" in t or "sistemas" in t: return "status"
        if "combate" in t: return "alert"
        return "passive"

    def _gerar_proximo_id(self, categoria: str) -> str:
        """
        Gera um ID único sequencial com verificação robusta de colisão.
        """
        count = 1
        ids_em_uso = set()
        
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                    # Adiciona as chaves principais e IDs internos
                    for k in dados.keys():
                        ids_em_uso.add(k.lower())
                    for v in dados.values():
                        if isinstance(v, dict) and "id" in v:
                            ids_em_uso.add(str(v["id"]).lower())
            except: pass

        while True:
            candidato = f"{categoria.lower()}_{count:02d}"
            if candidato in ids_em_uso:
                count += 1
            else:
                return candidato

    def _adicionar_a_fila(self, evento: Evento):
        texto = evento.dados.get("texto")
        if texto: self._queue.put(texto)

    def _aprender_e_catalogar(self, texto_original: str, chave: str) -> str:
        if not self.fish_api_key: return None

        # Limpa o texto base
        texto_limpo_api = texto_original.replace("_", " ").strip()
        
        emocao_analisada = "neutral"
        if self.voice_director:
            try: emocao_analisada = self.voice_director.analisar_tom(texto_original)
            except: pass

        categoria = self._determinar_categoria(texto_original)
        contexto_temporal = self._detectar_temporal(texto_original)
        sub_contexto = self._detectar_sub_contexto(texto_original, categoria)
        
        # --- LÓGICA DE INJEÇÃO DE EMOÇÃO (NOVO v2.6) ---
        # 1. Tenta pegar tag pela Categoria
        tag_emotion = FISH_TAGS.get(categoria, "")
        
        # 2. Se não tiver, pega pelo Sub-Contexto
        if not tag_emotion:
            tag_emotion = FISH_TAGS.get(sub_contexto, "")
            
        # 3. Monta o texto final para a API com ESPAÇAMENTO OBRIGATÓRIO
        # Ex: "(curious) Deseja algo?"
        if tag_emotion:
            texto_para_api = f"{tag_emotion} {texto_limpo_api}"
        else:
            texto_para_api = texto_limpo_api
            
        self.log.info(f"🎭 Payload API: '{texto_para_api}'")
        # -----------------------------------------------
        
        novo_id = self._gerar_proximo_id(categoria)
        nome_arquivo = f"{novo_id}.mp3"

        pasta_destino = os.path.join(self.audio_dir, categoria, contexto_temporal, sub_contexto)
        os.makedirs(pasta_destino, exist_ok=True)
        
        caminho_absoluto = os.path.join(pasta_destino, nome_arquivo)
        caminho_relativo = f"assets/{categoria}/{contexto_temporal}/{sub_contexto}/{nome_arquivo}"

        headers = {"Authorization": f"Bearer {self.fish_api_key}", "Content-Type": "application/json"}
        
        # Envia o texto COM A TAG para a API
        payload = {
            "text": texto_para_api, 
            "format": "mp3", 
            "latency": "balanced",
            "normalize": True, 
            "reference_id": self.fish_model_id if self.fish_model_id else None
        }

        try:
            self.log.info(f"🐟 Aprendendo: '{texto_para_api}' -> ID: {novo_id}")
            response = requests.post(FISH_AUDIO_API_URL, json=payload, headers=headers, timeout=15)
            
            if response.status_code == 200:
                with open(caminho_absoluto, "wb") as f: f.write(response.content)
                
                novo_registro = {
                    "id": novo_id, 
                    "text": texto_limpo_api, # Salva o texto limpo no JSON
                    "text_api": texto_para_api, # Salva o texto com tag enviado
                    "file_path": caminho_relativo,
                    "category": categoria, 
                    "key_hash": chave, 
                    "context": contexto_temporal,
                    "sub_context": sub_contexto, 
                    "emotion": emocao_analisada
                }
                self._salvar_indice(novo_registro)
                return caminho_absoluto
            else:
                self.log.error(f"Erro Fish Audio: {response.text}")
                return None
        except Exception as e:
            self.log.error(f"Erro Conexão: {e}")
            return None

    def _worker(self):
        while not self._stop_event.is_set():
            try:
                texto_original = self._queue.get(timeout=1.0)
                chave = self._normalizar_chave(texto_original)
                caminho_audio = None
                
                bus.publicar(Evento(Eventos.STATUS_FALA, {"status": True}))

                # 1. Tenta Cache Local
                if chave in self.voice_index:
                    entry = self.voice_index[chave]
                    path_rel = entry.get("file_path")
                    if path_rel:
                        path_rel = path_rel.replace("/", os.sep).replace("\\", os.sep)
                        abs_path = os.path.join(self.base_dir, path_rel)
                        if os.path.exists(abs_path):
                            self.log.info(f"💾 Memória: {entry.get('id')} ({entry.get('sub_context', 'old')})")
                            caminho_audio = abs_path

                # 2. Se não tem, Aprende
                if not caminho_audio:
                    caminho_audio = self._aprender_e_catalogar(texto_original, chave)

                # 3. Reproduz
                if caminho_audio and os.path.exists(caminho_audio):
                    self._reproduzir_audio_pygame(caminho_audio)
                else:
                    self._falar_offline(texto_original)
                
                bus.publicar(Evento(Eventos.STATUS_FALA, {"status": False}))
                self._queue.task_done()
            except queue.Empty: continue
            except Exception as e: self.log.error(f"Worker Error: {e}")

    def _reproduzir_audio_pygame(self, caminho):
        try:
            pygame.mixer.music.load(caminho)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy() and not self._stop_event.is_set():
                pygame.time.Clock().tick(10)
        except: pass

    def _falar_offline(self, texto):
        if self.engine_offline:
            try:
                self.engine_offline.say(texto)
                self.engine_offline.runAndWait()
            except: pass

    def start(self):
        if not self._thread or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._worker, daemon=True)
            self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)

mouth = NeuralSpeaker()