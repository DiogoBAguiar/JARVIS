import os
import json
import logging
import re
import unicodedata
from typing import Optional

try:
    from agno.agent import Agent
    from agno.models.groq import Groq
except ImportError:
    Agent = None
    Groq = None

# Imports Locais
from .llm_setup import LLMFactory
from .tools import SpotifyToolkit
from .limbic_system import LimbicSystem

logger = logging.getLogger("SPOTIFY_BRAIN")

class SpotifyBrain:
    def __init__(self, controller, consciencia):
        self.controller = controller
        self.consciencia = consciencia
        self.toolkit = SpotifyToolkit(controller, consciencia)
        self.limbic = LimbicSystem(controller)
        self.model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.agent = self._inicializar_agno()

    def _inicializar_agno(self) -> Optional[Agent]:
        if not Agent: return None
        llm = LLMFactory.get_model(self.model_name)
        if not llm and Groq:
            api_key = os.getenv("GROQ_API_KEY")
            if api_key: llm = Groq(id=self.model_name, api_key=api_key)
        if not llm: return None

        return Agent(
            model=llm,
            description="Você é o Cérebro do Spotify Jarvis. Decida a ação JSON.",
            instructions=[
                "Retorne APENAS um JSON válido.",
                "Formatos:",
                '1. {"acao": "tocar", "termo": "...", "tipo_estimado": "musica/artista/playlist"}',
                '   - "artista": Nomes de bandas, cantores.',
                '   - "playlist": Se contiver "playlist", "mix", "foco".',
                '   - "musica": Faixas específicas.',
                '2. {"acao": "consultar_memoria", "termo": "..."}',
                '3. {"acao": "comando", "tipo": "play/pause/next/prev"}',
                '4. {"acao": "abrir"}'
            ],
            markdown=False,
        )

    # --- DETECTOR DE RUÍDO (ASCII SAFE) ---
    def _detectar_gibberish(self, texto: str) -> bool:
        """
        Analisa se o texto parece ruído de teclado (ex: 'asdasd', 'kjjhkhk').
        """
        if not texto: return False
        t = texto.lower().strip()
        
        # 1. Regra "Home Row Spam" (Teclas do meio: a s d f g h j k l)
        # Removido 'ç' para compatibilidade Windows
        home_row = set("asdfghjkl") 
        letras_home_row = sum(1 for c in t if c in home_row)
        
        if len(t) > 0:
            ratio_home = letras_home_row / len(t)
            # Se mais de 85% das letras forem da linha do meio (ex: asdjasldkjaslkdj)
            if ratio_home > 0.85 and " " not in t and len(t) > 6:
                return True

        # 2. Análise de Vogais e Consoantes
        if " " not in t and len(t) > 8:
            max_consoantes = 0
            atual = 0
            # Vogais padrão sem acento para segurança
            vogais = "aeiouy" 
            
            # Normaliza para remover acentos antes de checar vogais
            t_norm = ''.join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')
            
            for char in t_norm:
                if char.isalpha() and char not in vogais:
                    atual += 1
                    max_consoantes = max(max_consoantes, atual)
                else:
                    atual = 0
            
            if max_consoantes > 5: return True

            num_vogais = sum(1 for c in t_norm if c in vogais)
            ratio = num_vogais / len(t)
            # Exige pelo menos 18% de vogais
            if len(t) > 5 and ratio < 0.18:
                return True

        # 3. Repetição excessiva
        for char in set(t):
            if char * 4 in t: return True

        # 4. Padrão de teclado
        if "qwer" in t or "asdf" in t or "zxcv" in t or "jkl" in t:
            if len(t) < 15: return True

        return False

    def processar(self, comando: str) -> str:
        if not comando: return ""
        
        # Limpeza básica
        termo_limpo = comando.lower().replace("jarvis", "").replace("tocar", "").strip()
        
        # --- BLOQUEIO DE RUÍDO ---
        if self._detectar_gibberish(termo_limpo):
            # Log INFO em vez de WARNING para não assustar o Manager
            logger.info(f"[Core] Input bloqueado por heuristica de ruido: '{termo_limpo}'")
            return "Infelizmente nao ouvi bem o que voce disse, poderia repetir?"

        # --- VIA RÁPIDA (LOCAL) ---
        acao_rapida = self._tentar_resolucao_local(comando)
        if acao_rapida:
            logger.info(f"⚡ Via Rápida acionada: Pulando LLM.")
            return acao_rapida

        # --- LLM (FALLBACK) ---
        if not self.agent: return self.limbic.reagir_instintivamente(comando)

        try:
            logger.info(f"🧠 [Córtex] Analisando: '{comando}'")
            resposta = self.agent.run(comando)
            texto_resp = getattr(resposta, 'content', str(resposta))
            texto_limpo = texto_resp.replace("```json", "").replace("```", "").strip()
            
            decisao = json.loads(texto_limpo)
            logger.info(f"🤔 Decisão Inicial IA: {decisao}")

            acao = decisao.get("acao")
            
            # Robustez para comandos diretos
            if acao in ["next", "proxima", "pular", "avançar", "proximo"]: return self.toolkit.proxima_faixa()
            if acao in ["prev", "previous", "anterior", "voltar"]: return self.toolkit.faixa_anterior()
            if acao in ["play", "pause", "continuar", "parar", "reproduzir"]: return self.toolkit.pausar_ou_continuar()

            if acao == "tocar":
                termo = decisao.get("termo") or decisao.get("musica")
                
                # Segunda checagem de ruído
                if self._detectar_gibberish(termo):
                    return "Infelizmente nao ouvi bem o que voce disse, poderia repetir?"

                tipo_ia = decisao.get("tipo_estimado", "musica").lower()
                
                is_artist_db = self.toolkit.verificar_se_artista(termo)
                if is_artist_db:
                    logger.info(f"📚 Confirmado pelo Banco: '{termo}' é um ARTISTA.")
                    return self.toolkit.tocar_musica(termo, tipo="artista")
                
                correcao = self.toolkit.sugerir_correcao(termo)
                if correcao:
                    logger.info(f"✨ Erro de audição corrigido: '{termo}' -> '{correcao}'")
                    return self.toolkit.tocar_musica(correcao, tipo="artista")
                
                return self.toolkit.tocar_musica(termo, tipo=tipo_ia)

            elif acao == "consultar_memoria":
                termo = decisao.get("termo")
                sugestao = self.toolkit.consultar_memoria_musical(termo)
                if "Encontrei" in sugestao:
                    musica_final = sugestao.split("'")[1] if "'" in sugestao else termo
                    return self.toolkit.tocar_musica(musica_final, tipo="musica")
                return self.toolkit.tocar_musica(termo, tipo="musica")
            
            elif acao == "comando":
                tipo = decisao.get("tipo")
                if "play" in tipo or "pause" in tipo: return self.toolkit.pausar_ou_continuar()
                if "next" in tipo: return self.toolkit.proxima_faixa()
                if "prev" in tipo: return self.toolkit.faixa_anterior()
                
            elif acao == "abrir":
                return self.toolkit.iniciar_aplicativo()

            return "Comando não compreendido."

        except Exception as e:
            logger.error(f"🔥 Erro no Router: {e}")
            return self.limbic.reagir_instintivamente(comando)

    def _normalizar(self, texto: str) -> str:
        return ''.join(c for c in unicodedata.normalize('NFD', texto.lower()) if unicodedata.category(c) != 'Mn')

    def _tentar_resolucao_local(self, comando: str) -> Optional[str]:
        cmd_full = comando.lower().strip()
        cmd_norm = self._normalizar(cmd_full)
        
        # 1. Comandos de Navegação (Incluindo 'pular faixa')
        comandos_next = ["proxima", "próxima", "pular", "avançar", "next", "pular faixa", "proxima faixa"]
        if any(c in cmd_full for c in comandos_next):
            return self.toolkit.proxima_faixa()
            
        if cmd_full in ["anterior", "voltar", "back", "prev"]: return self.toolkit.faixa_anterior()
        if cmd_full in ["pausar", "parar", "pause", "stop", "continuar", "play"]: return self.toolkit.pausar_ou_continuar()

        artistas_conhecidos = self.toolkit.db_artistas
        
        artista_encontrado = None
        artista_original_db = None
        termo_restante = cmd_full

        if artistas_conhecidos:
            for art in sorted(artistas_conhecidos, key=len, reverse=True):
                art_norm = self._normalizar(art)
                if art_norm in cmd_norm:
                    artista_encontrado = art_norm
                    artista_original_db = art
                    temp = cmd_norm.replace(art_norm, "")
                    temp = re.sub(r"^(jarvis,?)?\s*(tocar|ouvir|bota|põe|reproduzir|toca|escute)\s+", "", temp)
                    temp = re.sub(r"\s+(a[íi]|agora|por favor|pfv)$", "", temp)
                    temp = re.sub(r"\b(de|do|da|o|a)\b", "", temp)
                    termo_restante = temp.strip()
                    break
        
        if artista_original_db:
            logger.info(f"🎯 Vetor Artista identificado: '{artista_original_db}'. Resto: '{termo_restante}'")
            if termo_restante in ["um som", "som", "uma musica"]:
                musica_alvo = "O Som"
                return self.toolkit.tocar_musica(f"{musica_alvo} {artista_original_db}", tipo="musica")
            if not termo_restante:
                return self.toolkit.tocar_musica(artista_original_db, tipo="artista")
            return self.toolkit.tocar_musica(f"{termo_restante} {artista_original_db}", tipo="musica")

        padrao = r"(tocar|ouvir|som de|bota|reproduzir)\s+(.+)"
        match = re.search(padrao, cmd_full)
        if match:
            termo_bruto = match.group(2).strip()
            if self._detectar_gibberish(termo_bruto): return "Infelizmente nao ouvi bem o que voce disse, poderia repetir?"
            
            if self.toolkit.verificar_se_artista(termo_bruto):
                return self.toolkit.tocar_musica(termo_bruto, tipo="artista")
            correcao = self.toolkit.sugerir_correcao(termo_bruto)
            if correcao:
                return self.toolkit.tocar_musica(correcao, tipo="artista")

        return None