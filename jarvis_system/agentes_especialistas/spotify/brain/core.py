import os
import json
import logging
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
    """
    Cérebro Especialista em Música (Versão Híbrida: LLM + Verificação DB + Correção Fonética).
    """

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
                '1. {"acao": "tocar", "termo": "...", "tipo_estimado": "musica/artista"} -> Para pedidos de play.',
                '   - Use "tipo_estimado": "artista" se parecer um cantor/banda.',
                '   - Use "tipo_estimado": "musica" se parecer uma faixa.',
                '2. {"acao": "consultar_memoria", "termo": "..."} -> Pedidos vagos (ex: tocar algo triste).',
                '3. {"acao": "comando", "tipo": "play/pause/next/prev"}',
                '4. {"acao": "abrir"}'
            ],
            markdown=False,
        )

    def processar(self, comando: str) -> str:
        if not comando: return ""
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
                
                # --- INTELIGÊNCIA HÍBRIDA (NOVO BLOCO) ---
                
                # 1. Verifica no Banco de Dados (Soberania Local)
                is_artist_db = self.toolkit.verificar_se_artista(termo)
                
                if is_artist_db:
                    logger.info(f"📚 Confirmado pelo Banco: '{termo}' é um ARTISTA.")
                    tipo_final = "artista"
                else:
                    # 2. Tenta Correção Fonética (O pulo do gato!)
                    correcao = self.toolkit.sugerir_correcao(termo)
                    
                    if correcao:
                        logger.info(f"✨ Erro de audição corrigido: '{termo}' -> '{correcao}'")
                        termo = correcao # Substitui "Freio Gil Som" por "Frei Gilson"
                        tipo_final = "artista" # Se corrigiu pelo banco de artistas, é artista
                    else:
                        # 3. Fallback: Confia na IA
                        logger.info(f"🌐 Não encontrado no banco. Usando intuição da IA: {tipo_ia}")
                        tipo_final = tipo_ia
                
                return self.toolkit.tocar_musica(termo, tipo=tipo_final)

            elif acao == "consultar_memoria":
                termo = decisao.get("termo")
                sugestao = self.toolkit.consultar_memoria_musical(termo)
                logger.info(f"💡 Memória sugeriu: {sugestao}")
                if "Encontrei" in sugestao:
                    musica_final = sugestao.split("'")[1] if "'" in sugestao else termo
                    return self.toolkit.tocar_musica(musica_final, tipo="musica")
                else:
                    return self.toolkit.tocar_musica(termo, tipo="musica")
            
            elif acao == "comando":
                tipo = decisao.get("tipo")
                if "play" in tipo or "pause" in tipo: return self.toolkit.pausar_ou_continuar()
                if "next" in tipo: return self.toolkit.proxima_faixa()
                if "prev" in tipo: return self.toolkit.faixa_anterior()
                
            elif acao == "abrir":
                return self.toolkit.iniciar_aplicativo()

            return "Comando não compreendido."

        except json.JSONDecodeError:
            logger.warning(f"⚠️ IA não retornou JSON válido.")
            return self.limbic.reagir_instintivamente(comando)
        except Exception as e:
            logger.error(f"🔥 Erro no Router: {e}")
            return self.limbic.reagir_instintivamente(comando)