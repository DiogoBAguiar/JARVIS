import logging
import re
import unicodedata
from typing import Optional

# Imports Locais
from .tools import SpotifyToolkit
from .limbic_system import LimbicSystem

logger = logging.getLogger("SPOTIFY_BRAIN")

class SpotifyBrain:
    def __init__(self, controller, consciencia):
        self.controller = controller
        self.consciencia = consciencia
        self.toolkit = SpotifyToolkit(controller, consciencia)
        self.limbic = LimbicSystem(controller)
        logger.info("🧠 Motor Reativo do Spotify inicializado (Sem Duplo Cérebro LLM).")

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
        """
        Processamento Reativo (Sem LLM Interno).
        O Córtex Frontal já mastigou a intenção do utilizador.
        """
        if not comando: return ""
        
        termo_limpo = comando.lower().replace("jarvis", "").replace("tocar", "").strip()
        
        # 1. Filtro Anti-Ruído
        if self._detectar_gibberish(termo_limpo):
            logger.info(f"[Core] Input bloqueado por heuristica de ruido: '{termo_limpo}'")
            return "Infelizmente nao ouvi bem o que voce disse, poderia repetir?"

        try:
            # 2. Resolução Local Heurística (Fase 3: Limpeza e Vetorização)
            acao_local = self._tentar_resolucao_local(comando)
            
            if acao_local:
                logger.info(f"⚡ Resolução Local executada com sucesso.")
                return acao_local

            # 3. Fallback Final (Sistema Límbico)
            # Se a heurística local falhou completamente (o que é raro após a purga),
            # o sistema límbico instintivo assume.
            logger.warning(f"⚠️ Nenhuma heurística atendeu ao comando: '{comando}'. Acionando Sistema Límbico.")
            return self.limbic.reagir_instintivamente(comando)

        except Exception as e:
            logger.error(f"🔥 Erro no Router Reativo do Spotify: {e}")
            return self.limbic.reagir_instintivamente(comando)

    def _normalizar(self, texto: str) -> str:
        return ''.join(c for c in unicodedata.normalize('NFD', texto.lower()) if unicodedata.category(c) != 'Mn')

    def _tentar_resolucao_local(self, comando: str) -> Optional[str]:
        """
        Tenta resolver o comando usando heurísticas locais e banco de dados de artistas.
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
        cmd_limpo = re.sub(r"^(jarvis,?)?\s*(tocar|ouvir|bota|põe|reproduzir|toca|escute|play)\b", "", cmd_norm).strip()
        cmd_limpo = re.sub(r"\s+(a[íi]|agora|por favor|pfv)$", "", cmd_limpo).strip()
        
        if not cmd_limpo: return None

        # 4. Busca por Artista no Banco de Dados
        artistas_conhecidos = self.toolkit.db_artistas
        if artistas_conhecidos:
            for art in sorted(artistas_conhecidos, key=len, reverse=True):
                art_norm = self._normalizar(art)
                if art_norm in cmd_limpo:
                    termo_restante = cmd_limpo.replace(art_norm, "").replace(" de ", " ").strip()
                    
                    logger.info(f"🎯 Vetor Artista identificado: '{art}'. Resto: '{termo_restante}'")
                    
                    if not termo_restante or termo_restante in ["um som", "som", "uma musica"]:
                        return self.toolkit.tocar_musica(art, tipo="artista")
                    
                    return self.toolkit.tocar_musica(f"{termo_restante} {art}", tipo="musica")

        # 5. Fallback: Se não achou artista no banco, manda o termo limpo para a busca genérica
        logger.info(f"🔍 Busca Genérica Limpa: '{cmd_limpo}'")
        return self.toolkit.tocar_musica(cmd_limpo, tipo="musica")