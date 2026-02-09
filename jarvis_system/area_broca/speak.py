import os
import threading
import queue
import hashlib
import json
import pygame
import pyttsx3
import requests
import re
from dotenv import load_dotenv

# Core Imports
from jarvis_system.cortex_frontal.observability import JarvisLogger
from jarvis_system.cortex_frontal.event_bus import bus, Evento
from jarvis_system.protocol import Eventos
from jarvis_system.area_broca.frases_padrao import FRASES_DO_SISTEMA

load_dotenv()

FISH_AUDIO_API_URL = "https://api.fish.audio/v1/tts"

class NeuralSpeaker:
    def __init__(self):
        self.log = JarvisLogger("BROCA_VOICE")
        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread = None
        
        self.fish_api_key = os.getenv("FISHAUDIO_API_KEY")
        self.fish_model_id = os.getenv("FISHAUDIO_MODEL_ID")

        # --- DIRETÓRIOS ---
        # Ajustado para sua estrutura: PROJETO/jarvis_system/data/voices
        self.base_dir = os.path.join(os.getcwd(), "jarvis_system", "data", "voices")
        self.audio_dir = os.path.join(self.base_dir, "assets")
        self.index_path = os.path.join(self.base_dir, "voice_index.json")
        
        os.makedirs(self.audio_dir, exist_ok=True)

        self.voice_index = {} 
        self._carregar_indice()

        try: pygame.mixer.init()
        except: pass
        self.engine_offline = pyttsx3.init()
        
        bus.inscrever(Eventos.FALAR, self._adicionar_a_fila)

    def _normalizar_chave(self, texto: str) -> str:
        if not texto: return ""
        texto = re.sub(r'\([^)]*\)', '', texto)
        texto = texto.lower()
        texto = texto.replace('á', 'a').replace('à', 'a').replace('ã', 'a').replace('â', 'a')
        texto = texto.replace('é', 'e').replace('ê', 'e')
        texto = texto.replace('í', 'i')
        texto = texto.replace('ó', 'o').replace('õ', 'o').replace('ô', 'o')
        texto = texto.replace('ú', 'u')
        texto = texto.replace('ç', 'c')
        return re.sub(r'[^a-z0-9]', '', texto)

    def _carregar_indice(self):
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item_id, metadata in data.items():
                        chave = metadata.get("key_hash")
                        if chave:
                            self.voice_index[chave] = metadata
                self.log.info(f"📂 Índice Vocal Carregado: {len(self.voice_index)} frases.")
            except Exception as e:
                self.log.error(f"Erro ao ler voice_index.json: {e}")
                self.voice_index = {}
        else:
            self.log.warning("⚠️ voice_index.json não encontrado.")

    def _salvar_indice(self, novo_dado: dict):
        dados_atuais = {}
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    dados_atuais = json.load(f)
            except: pass
        
        item_id = novo_dado["id"]
        dados_atuais[item_id] = novo_dado
        
        with open(self.index_path, 'w', encoding='utf-8') as f:
            json.dump(dados_atuais, f, indent=4, ensure_ascii=False)
            
        self.voice_index[novo_dado["key_hash"]] = novo_dado

    def _determinar_categoria(self, texto_limpo: str) -> str:
        chave_procurada = self._normalizar_chave(texto_limpo)
        for categoria, lista_frases in FRASES_DO_SISTEMA.items():
            for frase in lista_frases:
                if self._normalizar_chave(frase) == chave_procurada:
                    return categoria
        return "GENERICO"

    # --- NOVO: Lógica de Detecção de Contexto ---
    def _detectar_contexto(self, texto: str) -> str:
        """Detecta contexto temporal ou situacional."""
        t = texto.lower().replace("_", " ")
        
        # Lógica Temporal
        if "bom dia" in t: return "morning"
        if "boa tarde" in t: return "afternoon"
        if "boa noite" in t: return "night"
        
        # Futuro: Adicione aqui lógicas para subcontextos se desejar
        # ex: if "saindo" in t: return "exit"
        
        return "any"

    def _gerar_proximo_id(self, categoria: str) -> str:
        count = 1
        dados_existentes = {}
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    dados_existentes = json.load(f)
            except: pass

        while True:
            candidato = f"{categoria.lower()}_{count:02d}"
            if candidato not in dados_existentes:
                return candidato
            count += 1

    def _adicionar_a_fila(self, evento: Evento):
        texto = evento.dados.get("texto")
        if texto: self._queue.put(texto)

    def _aprender_e_catalogar(self, texto_original: str, chave: str) -> str:
        if not self.fish_api_key: return None

        texto_limpo_api = texto_original.replace("_", " ")

        # 1. Metadados Inteligentes
        categoria = self._determinar_categoria(texto_original)
        contexto = self._detectar_contexto(texto_original)
        # sub_contexto = "" # Espaço reservado para lógica futura

        novo_id = self._gerar_proximo_id(categoria)
        nome_arquivo = f"{novo_id}.mp3"

        # 2. Definição da Pasta Profunda (assets/CATEGORIA/contexto/)
        pasta_destino = os.path.join(self.audio_dir, categoria, contexto)
        
        # Se tivesse subcontexto, seria:
        # pasta_destino = os.path.join(self.audio_dir, categoria, contexto, sub_contexto)

        os.makedirs(pasta_destino, exist_ok=True)
        
        caminho_absoluto = os.path.join(pasta_destino, nome_arquivo)
        # Caminho relativo para o JSON (com barras normais /)
        caminho_relativo = f"assets/{categoria}/{contexto}/{nome_arquivo}"

        # 3. API Fish Audio
        headers = {"Authorization": f"Bearer {self.fish_api_key}", "Content-Type": "application/json"}
        payload = {
            "text": texto_limpo_api,
            "format": "mp3",
            "latency": "balanced",
            "normalize": True,
            "reference_id": self.fish_model_id if self.fish_model_id else None
        }

        try:
            self.log.info(f"🐟 Aprendendo: [{categoria}/{contexto}] '{texto_limpo_api[:25]}...'")
            response = requests.post(FISH_AUDIO_API_URL, json=payload, headers=headers, timeout=15)
            
            if response.status_code == 200:
                with open(caminho_absoluto, "wb") as f:
                    f.write(response.content)
                
                novo_registro = {
                    "id": novo_id,
                    "text": texto_limpo_api,
                    "file_path": caminho_relativo,
                    "category": categoria,
                    "key_hash": chave,
                    "context": contexto,
                    # "sub_context": sub_contexto
                }
                
                self._salvar_indice(novo_registro)
                self.log.info(f"✅ Salvo: {caminho_relativo}")
                return caminho_absoluto
            else:
                self.log.error(f"Erro API: {response.text}")
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

                if chave in self.voice_index:
                    entry = self.voice_index[chave]
                    # Reconstrói caminho absoluto
                    path_rel = entry.get("file_path")
                    # Corrige barras para o SO atual
                    path_rel = path_rel.replace("/", os.sep).replace("\\", os.sep)
                    abs_path = os.path.join(self.base_dir, path_rel)
                    
                    if os.path.exists(abs_path):
                        self.log.info(f"🗂️ Índice Hit: [{entry['id']}]")
                        caminho_audio = abs_path
                    else:
                        self.log.warning(f"Arquivo sumiu: {abs_path}")

                if not caminho_audio:
                    caminho_audio = self._aprender_e_catalogar(texto_original, chave)

                if caminho_audio and os.path.exists(caminho_audio):
                    self._reproduzir_audio_pygame(caminho_audio)
                else:
                    texto_limpo = re.sub(r'\([^)]*\)', '', texto_original)
                    self._falar_offline(texto_limpo)
                
                bus.publicar(Evento(Eventos.STATUS_FALA, {"status": False}))
                self._queue.task_done()

            except queue.Empty: continue
            except Exception as e:
                self.log.error(f"Erro worker: {e}")

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