import os
import json
import logging
import re
import unicodedata # <--- NOVO: Para lidar com "Matue" vs "Matuê"
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

    def processar(self, comando: str) -> str:
        if not comando: return ""
        
        # --- VIA RÁPIDA (LOCAL FIRST) ---
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
            
            if acao == "tocar":
                termo = decisao.get("termo") or decisao.get("musica")
                tipo_ia = decisao.get("tipo_estimado", "musica").lower()
                
                # Inteligência Híbrida
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
        """Remove acentos e minúsculas para comparação (Matuê -> matue)."""
        return ''.join(c for c in unicodedata.normalize('NFD', texto.lower()) if unicodedata.category(c) != 'Mn')

    def _tentar_resolucao_local(self, comando: str) -> Optional[str]:
        """
        Lógica vetorial avançada: Extrai Artista e interpreta o contexto ("um som" -> "O Som").
        """
        cmd_full = comando.lower().strip()
        cmd_norm = self._normalizar(cmd_full) # Versão sem acentos para busca
        
        # 1. Comandos de Navegação
        if cmd_full in ["proxima", "próxima", "pular", "avançar", "next"]:
            return self.toolkit.proxima_faixa()
        if cmd_full in ["anterior", "voltar", "back", "prev"]:
            return self.toolkit.faixa_anterior()
        if cmd_full in ["pausar", "parar", "pause", "stop", "continuar", "play"]:
            return self.toolkit.pausar_ou_continuar()

        # 2. Extração Vetorial (Busca Artista na frase)
        artistas_conhecidos = self.toolkit.db_artistas
        
        artista_encontrado = None
        artista_original_db = None
        termo_restante = cmd_full

        if artistas_conhecidos:
            # Ordena por tamanho para pegar "Legião Urbana" antes de "Legião"
            for art in sorted(artistas_conhecidos, key=len, reverse=True):
                art_norm = self._normalizar(art)
                # Verifica se o artista (sem acento) está no comando (sem acento)
                if art_norm in cmd_norm:
                    artista_encontrado = art_norm
                    artista_original_db = art # Guarda o nome bonitinho (com acento)
                    
                    # Remove o artista da frase original normalizada para ver o que sobra
                    # Ex: "bota um som de matue ai" - "matue" = "bota um som de  ai"
                    temp = cmd_norm.replace(art_norm, "")
                    
                    # Limpeza agressiva de stopwords
                    temp = re.sub(r"^(jarvis,?)?\s*(tocar|ouvir|bota|põe|reproduzir|toca|escute)\s+", "", temp)
                    temp = re.sub(r"\s+(a[íi]|agora|por favor|pfv)$", "", temp)
                    temp = re.sub(r"\b(de|do|da|o|a)\b", "", temp) # Remove preposições
                    termo_restante = temp.strip()
                    break
        
        # Lógica de Decisão baseada no que sobrou
        if artista_original_db:
            logger.info(f"🎯 Vetor Artista identificado: '{artista_original_db}'. Resto: '{termo_restante}'")
            
            # Caso A: Resto é "um som" ou "som" -> Mapeia para "O Som" (Sua lógica desejada)
            if termo_restante in ["um som", "som", "uma musica"]:
                musica_alvo = "O Som"
                logger.info(f"✨ [Intuição] '{termo_restante}' mapeado para música '{musica_alvo}' de {artista_original_db}")
                # Busca: "O Som Matuê"
                return self.toolkit.tocar_musica(f"{musica_alvo} {artista_original_db}", tipo="musica")
            
            # Caso B: Resto vazio -> Tocar Artista (Shuffle)
            if not termo_restante:
                return self.toolkit.tocar_musica(artista_original_db, tipo="artista")
            
            # Caso C: Resto específico -> Tocar Música/Playlist
            # Ex: "tocar playlist foco de coldplay" -> resto="playlist foco"
            return self.toolkit.tocar_musica(f"{termo_restante} {artista_original_db}", tipo="musica")

        # 3. Fallback: Se não achou artista no loop acima, tenta regex simples
        padrao = r"(tocar|ouvir|som de|bota|reproduzir)\s+(.+)"
        match = re.search(padrao, cmd_full)
        if match:
            termo_bruto = match.group(2).strip()
            
            # Verifica se o termo inteiro é um artista (Ex: "Tocar Matuê")
            if self.toolkit.verificar_se_artista(termo_bruto):
                return self.toolkit.tocar_musica(termo_bruto, tipo="artista")
            
            # Correção fonética
            correcao = self.toolkit.sugerir_correcao(termo_bruto)
            if correcao:
                logger.info(f"✨ [Via Rápida] Correção fonética aplicada: '{termo_bruto}' -> '{correcao}'")
                return self.toolkit.tocar_musica(correcao, tipo="artista")

        return None