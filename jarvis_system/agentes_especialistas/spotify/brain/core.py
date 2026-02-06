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
        cmd_full = comando.lower().strip()
        cmd_norm = self._normalizar(cmd_full)
        palavras = set(cmd_full.split()) # Tokenização para evitar bugs como "coldplay" conter "play"
        
        # 1. Comandos de Navegação Simples (Next/Prev)
        if any(c in palavras for c in ["proxima", "pular", "next", "avançar"]): return self.toolkit.proxima_faixa()
        if any(c in palavras for c in ["anterior", "voltar", "prev", "back"]): return self.toolkit.faixa_anterior()
        
        # 2. Comando Play/Pause INTELIGENTE
        # Só aciona o Play/Pause se NÃO houver indicio de busca (ex: "tocar coldplay")
        cmds_pause = {"pausar", "parar", "pause", "stop", "continuar", "play", "resume"}
        
        # Interseção: Verifica se tem alguma palavra de comando
        if not palavras.isdisjoint(cmds_pause):
            # Remove palavras "inúteis" para ver se sobra algo (o nome da música)
            termos_uteis = [p for p in palavras if p not in ["jarvis", "o", "a", "por", "favor", "agora", "som"]]
            
            # Se a única palavra útil for o comando (ex: "jarvis play"), então é Play/Pause.
            # Se sobrar "coldplay" (ex: "play coldplay"), ele ignora aqui e deixa ir para a busca.
            cmd_encontrado = next((c for c in termos_uteis if c in cmds_pause), None)
            if cmd_encontrado and len(termos_uteis) <= 1:
                return self.toolkit.pausar_ou_continuar()

        # 3. Comandos de Informação
        if any(c in cmd_full for c in ["que musica", "o que esta tocando", "nome da musica"]):
             info = self.controller.ler_musica_atual()
             if info and info.get('track'):
                 return f"Esta é {info['track']} de {info['artist']}."
             return "Não consegui ler o nome da música agora."

        # 4. Busca por Artista (Banco de Dados Local)
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
                    # Remove verbos de ação para limpar o termo
                    temp = re.sub(r"^(jarvis,?)?\s*(tocar|ouvir|bota|põe|reproduzir|toca|escute|play)\s+", "", temp)
                    temp = re.sub(r"\s+(a[íi]|agora|por favor|pfv)$", "", temp)
                    temp = re.sub(r"\b(de|do|da|o|a)\b", "", temp)
                    termo_restante = temp.strip()
                    break
        
        if artista_original_db:
            logger.info(f"🎯 Vetor Artista identificado: '{artista_original_db}'. Resto: '{termo_restante}'")
            if termo_restante in ["um som", "som", "uma musica", ""]:
                return self.toolkit.tocar_musica(artista_original_db, tipo="artista")
            return self.toolkit.tocar_musica(f"{termo_restante} {artista_original_db}", tipo="musica")

        # 5. Regex de Busca Genérica
        padrao = r"(tocar|ouvir|som de|bota|reproduzir|play)\s+(.+)"
        match = re.search(padrao, cmd_full)
        if match:
            termo_bruto = match.group(2).strip()
            if self._detectar_gibberish(termo_bruto): return "Infelizmente nao ouvi bem o que voce disse, poderia repetir?"
            
            if self.toolkit.verificar_se_artista(termo_bruto):
                return self.toolkit.tocar_musica(termo_bruto, tipo="artista")
            correcao = self.toolkit.sugerir_correcao(termo_bruto)
            if correcao:
                return self.toolkit.tocar_musica(correcao, tipo="artista")
            
            # Se não reconheceu artista, toca como busca genérica (Web Driver vai resolver)
            return self.toolkit.tocar_musica(termo_bruto, tipo="musica")

        return None