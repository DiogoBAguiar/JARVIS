import requests
from .base_agente import AgenteEspecialista

# Importamos o cérebro para usar a inteligência do Groq
try:
    from jarvis_system.cortex_frontal.brain_llm import llm
except ImportError:
    llm = None

class AgenteClima(AgenteEspecialista):
    @property
    def nome(self):
        return "clima"

    @property
    def gatilhos(self):
        return [
            "clima", "tempo", "temperatura", "vai chover", "previsão", 
            "chuva", "sol", "nublado", "umidade", "frio", "quente", "calor"
        ]

    def _extrair_cidade_com_llm(self, comando: str) -> str:
        """
        Usa o Groq para limpar a sujeira do Whisper e achar a cidade.
        Ex: "clima em jom pessoa" -> "João Pessoa"
        """
        if not llm:
            return "AUTO"

        prompt = f"""
        Tarefa: Analise o comando do usuário e extraia o nome da cidade para previsão do tempo.
        Comando: "{comando}"
        
        Regras:
        1. Corrija erros fonéticos (ex: "jom pessoa" -> "João Pessoa", "o pessoal" -> "João Pessoa", "recifei" -> "Recife").
        2. Se não houver cidade citada, responda exatamente: AUTO.
        3. Responda APENAS o nome da cidade formatado corretamente. Sem frases, sem explicações.
        """
        
        # O LLM pensa...
        resposta = llm.pensar(prompt).strip().replace(".", "")
        
        # Limpeza extra caso o LLM seja tagarela
        if "auto" in resposta.lower() or len(resposta) > 50:
            return "AUTO"
        
        return resposta

    def executar(self, comando: str, **kwargs) -> str:
        # 1. Inteligência: Pergunta ao Groq qual é a cidade
        cidade_destino = self._extrair_cidade_com_llm(comando)
        
        # 2. Define a URL
        if cidade_destino == "AUTO":
            # Usa IP
            url = "https://wttr.in/?format=j1&lang=pt"
            modo_auto = True
        else:
            # Usa a cidade corrigida pelo Groq (ex: "João Pessoa")
            url = f"https://wttr.in/{cidade_destino}?format=j1&lang=pt"
            modo_auto = False

        try:
            # Timeout curto para não travar o Jarvis se a internet oscilar
            response = requests.get(url, timeout=8)
            
            if response.status_code != 200:
                return "O satélite meteorológico não respondeu. Tente novamente."

            dados = response.json()
            
            # 3. Confirmação do Local
            local_formatado = cidade_destino
            
            if 'nearest_area' in dados:
                try:
                    area = dados['nearest_area'][0]
                    cidade_api = area['areaName'][0]['value']
                    
                    if modo_auto:
                        local_formatado = cidade_api
                    else:
                        # Se o Groq mandou "João Pessoa", usamos isso para ficar bonito na fala
                        local_formatado = cidade_destino
                except: pass

            # 4. Dados do Clima
            atual = dados['current_condition'][0]
            previsao_hoje = dados['weather'][0]
            
            temp = atual['temp_C']
            desc = atual['lang_pt'][0]['value']
            umidade = atual['humidity']
            maxima = previsao_hoje['maxtempC']
            minima = previsao_hoje['mintempC']
            
            texto = (
                f"Em {local_formatado}, faz {temp} graus e o céu está {desc}. "
                f"A umidade é de {umidade}%. "
                f"Máxima de {maxima} e mínima de {minima} para hoje."
            )
            return texto

        except requests.exceptions.ReadTimeout:
            return "A conexão com o serviço de tempo expirou. A internet pode estar lenta."
        except Exception as e:
            print(f"[ERRO CLIMA] {e}")
            return f"Não consegui verificar o clima para {cidade_destino}."