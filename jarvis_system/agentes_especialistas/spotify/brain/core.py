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
                '2. {"acao": "consultar_memoria", "termo": "..."}',
                '3. {"acao": "comando", "tipo": "play/pause/next/prev/like"}',
                '4. {"acao": "abrir"}',
                '5. {"acao": "consultar_estado"}'
            ],
            markdown=False,
        )

    # --- DETECTOR DE RUÍDO (ASCII SAFE) ---
    def _detectar_gibberish(self, texto: str) -> bool:
        if not texto: return False
        t = texto.lower().strip()
        
        home_row = set("asdfghjkl") 
        letras_home_row = sum(1 for c in t if c in home_row)
        
        if len(t) > 0:
            ratio_home = letras_home_row / len(t)
            if ratio_home > 0.85 and " " not in t and len(t) > 6:
                return True

        if " " not in t and len(t) > 8:
            max_consoantes = 0
            atual = 0
            vogais = "aeiouy" 
            t_norm = ''.join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')
            
            for char in t_norm:
                if char.isalpha() and char not in vogais:
                    atual += 1
                    max_consoantes = max(max_consoantes, atual)
                else:
                    atual = 0
            
            if max_consoantes > 5: return True

        for char in set(t):
            if char * 4 in t: return True

        if "qwer" in t or "asdf" in t or "zxcv" in t or "jkl" in t:
            if len(t) < 15: return True

        return False

    def processar(self, comando: str) -> str:
        if not comando: return ""
        
        termo_limpo = comando.lower().replace("jarvis", "").replace("tocar", "").strip()
        
        if self._detectar_gibberish(termo_limpo):
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
            
            try:
                decisao = json.loads(texto_limpo)
            except:
                decisao = {"acao": "tocar", "termo": comando, "tipo_estimado": "musica"}

            logger.info(f"🤔 Decisão Inicial IA: {decisao}")

            acao = decisao.get("acao")
            
            if acao == "consultar_estado":
                info = self.controller.ler_musica_atual()
                if info and info.get('track'):
                    return f"Atualmente tocando: {info['track']} de {info['artist']}."
                return "Não consegui identificar a música tocando no momento."

            if acao in ["next", "proxima", "pular", "avançar", "proximo"]: return self.toolkit.proxima_faixa()
            if acao in ["prev", "previous", "anterior", "voltar"]: return self.toolkit.faixa_anterior()
            if acao in ["play", "pause", "continuar", "parar", "reproduzir"]: return self.toolkit.pausar_ou_continuar()
            if acao in ["like", "curtir", "favoritar"]: return self.toolkit.curtir_musica()

            if acao == "tocar":
                termo = decisao.get("termo") or decisao.get("musica") or comando
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
                if "like" in tipo: return self.toolkit.curtir_musica()
                
            elif acao == "abrir":
                return self.toolkit.iniciar_aplicativo()

            return "Comando não compreendido."

        except Exception as e:
            logger.error(f"🔥 Erro no Router: {e}")
            return self.limbic.reagir_instintivamente(comando)

    def _normalizar(self, texto: str) -> str:
        return ''.join(c for c in unicodedata.normalize('NFD', texto.lower()) if unicodedata.category(c) != 'Mn')

    def _tentar_resolucao_local(self, comando: str) -> Optional[str]:
        """
        Tenta resolver o comando usando heurísticas locais e banco de dados de artistas.
        Refatorado para limpar o ruído (Fase 3) antes da identificação.
        """
        cmd_full = comando.lower().strip()
        cmd_norm = self._normalizar(cmd_full)
        palavras = set(cmd_full.split())
        
        # 1. Comandos de Navegação Simples (Next/Prev)
        if any(c in palavras for c in ["proxima", "pular", "next", "avançar"]): return self.toolkit.proxima_faixa()
        if any(c in palavras for c in ["anterior", "voltar", "prev", "back"]): return self.toolkit.faixa_anterior()
        
        # 2. Comando Play/Pause Inteligente
        cmds_pause = {"pausar", "parar", "pause", "stop", "continuar", "play", "resume"}
        if not palavras.isdisjoint(cmds_pause):
            termos_uteis = [p for p in palavras if p not in ["jarvis", "o", "a", "por", "favor", "agora", "som"]]
            cmd_encontrado = next((c for c in termos_uteis if c in cmds_pause), None)
            if cmd_encontrado and len(termos_uteis) <= 1:
                return self.toolkit.pausar_ou_continuar()

        # 3. Comandos de Informação
        if any(c in cmd_full for c in ["que musica", "o que esta tocando", "nome da musica"]):
             info = self.controller.ler_musica_atual()
             if info and info.get('track'):
                 return f"Esta é {info['track']} de {info['artist']}."
             return "Não consegui ler o nome da música agora."

        # --- FASE 3: PURGA DE RUÍDO (LIMPEZA DE PREFIXO) ---
        # Removemos Jarvis e verbos de ação para não poluir a identificação do artista.
        cmd_limpo = re.sub(r"^(jarvis,?)?\s*(tocar|ouvir|bota|põe|reproduzir|toca|escute|play)\b", "", cmd_norm).strip()
        cmd_limpo = re.sub(r"\s+(a[íi]|agora|por favor|pfv)$", "", cmd_limpo).strip()
        
        if not cmd_limpo: return None

        # 4. Busca por Artista no Banco de Dados (Agora com o comando limpo!)
        artistas_conhecidos = self.toolkit.db_artistas
        if artistas_conhecidos:
            # Procuramos o artista dentro do que sobrou da frase limpa
            for art in sorted(artistas_conhecidos, key=len, reverse=True):
                art_norm = self._normalizar(art)
                if art_norm in cmd_limpo:
                    # Se achou o artista, extrai o que sobrou (ex: "Sparks" de "Sparks Coldplay")
                    termo_restante = cmd_limpo.replace(art_norm, "").replace(" de ", " ").strip()
                    
                    logger.info(f"🎯 Vetor Artista identificado: '{art}'. Resto: '{termo_restante}'")
                    
                    if not termo_restante or termo_restante in ["um som", "som", "uma musica"]:
                        return self.toolkit.tocar_musica(art, tipo="artista")
                    
                    # Toca "Musica + Artista" para maior precisão no fallback
                    return self.toolkit.tocar_musica(f"{termo_restante} {art}", tipo="musica")

        # 5. Fallback: Se não achou artista no banco, manda o termo limpo para a busca genérica
        logger.info(f"🔍 Busca Genérica Limpa: '{cmd_limpo}'")
        return self.toolkit.tocar_musica(cmd_limpo, tipo="musica")