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
    Cérebro Especialista em Música (Versão JSON Puro).
    Evita o uso de 'Tools' nativas da API para prevenir erros de XML.
    O Cérebro apenas decide o JSON, e este código executa.
    """

    def __init__(self, controller, consciencia):
        self.controller = controller
        self.consciencia = consciencia
        self.toolkit = SpotifyToolkit(controller, consciencia)
        self.limbic = LimbicSystem(controller)
        
        # Modelo mais robusto para JSON
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
            description="Você é o Cérebro do Spotify Jarvis. Você recebe um comando e decide qual função JSON retornar.",
            instructions=[
                "Analise o pedido do usuário e retorne APENAS um JSON válido.",
                "Não escreva nada antes ou depois do JSON.",
                "Formatos possíveis:",
                '1. {"acao": "consultar_memoria", "termo": "..."} -> Se o pedido for vago (ex: tocar rock, tocar algo animado).',
                '2. {"acao": "tocar", "musica": "..."} -> Se o pedido for específico (ex: tocar Queen, tocar Anitta).',
                '3. {"acao": "comando", "tipo": "play/pause/next/prev"} -> Para controles de playback.',
                '4. {"acao": "abrir"} -> Para abrir o Spotify.'
            ],
            markdown=False,
            # SEM TOOLS! Vamos fazer o routing manualmente.
        )

    def processar(self, comando: str) -> str:
        """Pipeline de Execução Manual."""
        if not comando: return ""
        if not self.agent: return self.limbic.reagir_instintivamente(comando)

        try:
            logger.info(f"🧠 [Córtex] Analisando: '{comando}'")
            
            # 1. Pede decisão para a IA
            resposta = self.agent.run(comando)
            texto_resp = getattr(resposta, 'content', str(resposta))
            
            # Limpa markdown de código json ```json ... ```
            texto_limpo = texto_resp.replace("```json", "").replace("```", "").strip()
            
            # 2. Parse do JSON
            decisao = json.loads(texto_limpo)
            logger.info(f"🤔 Decisão: {decisao}")

            # 3. Roteamento (Router)
            acao = decisao.get("acao")
            
            if acao == "consultar_memoria":
                termo = decisao.get("termo")
                # Chama a memória manualmente
                sugestao = self.toolkit.consultar_memoria_musical(termo)
                logger.info(f"💡 Memória sugeriu: {sugestao}")
                # Se a memória devolveu algo útil, toca. Se não, busca o termo original.
                if "Encontrei" in sugestao:
                    # Extrai o nome da música da resposta da tool (hack rápido)
                    musica_final = sugestao.split("'")[1] if "'" in sugestao else termo
                    return self.toolkit.tocar_musica(musica_final)
                else:
                    return self.toolkit.tocar_musica(termo)

            elif acao == "tocar":
                return self.toolkit.tocar_musica(decisao.get("musica"))
            
            elif acao == "comando":
                tipo = decisao.get("tipo")
                if "play" in tipo or "pause" in tipo: return self.toolkit.pausar_ou_continuar()
                if "next" in tipo: return self.toolkit.proxima_faixa()
                if "prev" in tipo: return self.toolkit.faixa_anterior()
                
            elif acao == "abrir":
                return self.toolkit.iniciar_aplicativo()

            return "Comando não compreendido."

        except json.JSONDecodeError:
            logger.warning(f"⚠️ IA não retornou JSON válido: {texto_resp}")
            return self.limbic.reagir_instintivamente(comando)
            
        except Exception as e:
            logger.error(f"🔥 Erro no Router: {e}")
            return self.limbic.reagir_instintivamente(comando)