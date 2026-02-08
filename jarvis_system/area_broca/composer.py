import os
from pydub import AudioSegment
from jarvis_system.cortex_frontal.observability import JarvisLogger

class VoiceComposer:
    def __init__(self):
        self.log = JarvisLogger("BROCA_COMPOSER")
        self.bank_path = os.path.join(os.path.dirname(__file__), "voice_bank")
        
        # Cache na RAM para velocidade extrema (áudios pequenos)
        self.audio_cache = {} 
        self._carregar_banco()

    def _carregar_banco(self):
        """Carrega todos os wavs para a memória RAM no boot."""
        if not os.path.exists(self.bank_path):
            os.makedirs(self.bank_path)
            return

        for palavra in os.listdir(self.bank_path):
            pasta_palavra = os.path.join(self.bank_path, palavra)
            if os.path.isdir(pasta_palavra):
                self.audio_cache[palavra] = {}
                for arquivo in os.listdir(pasta_palavra):
                    emoção = arquivo.split('.')[0] # ex: 'urgente.wav' -> 'urgente'
                    caminho = os.path.join(pasta_palavra, arquivo)
                    try:
                        audio = AudioSegment.from_wav(caminho)
                        self.audio_cache[palavra][emoção] = audio
                    except Exception as e:
                        self.log.error(f"Erro ao carregar {caminho}: {e}")
        
        self.log.info(f"🎹 Maestro carregado: {len(self.audio_cache)} palavras no banco.")

    def compor_frase(self, texto: str, emocao: str = "neutro") -> str:
        """
        Recebe texto (ex: 'sistemas online senhor') e emoção.
        Retorna o caminho de um arquivo temporário costurado.
        """
        palavras = texto.lower().split()
        audio_final = AudioSegment.empty()
        
        usou_banco = False # Flag para saber se conseguimos montar algo

        for i, palavra in enumerate(palavras):
            segmento = self._buscar_segmento(palavra, emocao)
            
            if segmento:
                # Adiciona um pequeno silêncio (50ms) entre palavras para naturalidade
                if len(audio_final) > 0:
                    audio_final += AudioSegment.silent(duration=50)
                
                # Crossfade de 10ms para evitar 'cliques' no áudio
                audio_final = audio_final.append(segmento, crossfade=10)
                usou_banco = True
            else:
                # O Pulo do Gato: Se faltar UMA palavra, essa estratégia complexa falha.
                # Para MVP, se faltar palavra, retornamos None e deixamos o Edge-TTS falar tudo.
                # Numa versão V2, poderiamos misturar TTS com Wav, mas é difícil sincronizar.
                self.log.debug(f"Palavra '{palavra}' não existe no banco. Abortando composição.")
                return None

        if not usou_banco: return None

        # Exporta o resultado
        output_path = os.path.join(os.getcwd(), "temp_composed.wav")
        audio_final.export(output_path, format="wav")
        return output_path

    def _buscar_segmento(self, palavra: str, emocao_alvo: str):
        """Tenta achar a emoção exata. Se não tiver, tenta neutro."""
        if palavra not in self.audio_cache:
            return None
        
        variacoes = self.audio_cache[palavra]
        
        # 1. Tenta a emoção pedida (ex: "urgente")
        if emocao_alvo in variacoes:
            return variacoes[emocao_alvo]
        
        # 2. Fallback para "neutro"
        if "neutro" in variacoes:
            return variacoes["neutro"]
            
        # 3. Pega qualquer uma que tiver
        if len(variacoes) > 0:
            return list(variacoes.values())[0]
            
        return None