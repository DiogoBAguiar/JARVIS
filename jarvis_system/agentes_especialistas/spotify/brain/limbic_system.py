import logging

logger = logging.getLogger("SPOTIFY_LIMBIC")

class LimbicSystem:
    """
    Sistema de Resposta Rápida (Fallback).
    Atua quando a LLM está indisponível, lenta ou confusa.
    Não usa IA, usa instinto (padrões de texto).
    """

    def __init__(self, controller):
        self.controller = controller

    def reagir_instintivamente(self, comando: str) -> str:
        """Processamento baseado em regras (Sem IA)."""
        cmd = comando.lower().strip()
        logger.warning(f"⚠️ Ativando Sistema Límbico (Fallback) para: '{cmd}'")

        if not self.controller:
            return "Erro: Sistema motor (Controller) desconectado."

        try:
            # 1. Abrir App
            if any(x in cmd for x in ["abrir", "iniciar", "lançar"]) and "spotify" in cmd:
                self.controller.launch_app()
                return "Abrindo Spotify (Modo Instintivo)."

            # 2. Navegação Básica
            if "proxima" in cmd or "pular" in cmd:
                self.controller.next_track()
                return "Pulei a faixa."
            
            if "pausa" in cmd or "parar" in cmd or "continuar" in cmd:
                self.controller.resume()
                return "Play/Pause acionado."

            # 3. Tentativa de Busca (Extração simples)
            # Remove palavras comuns para achar o nome da música
            gatilhos = ["tocar", "toque", "play", "ouve", "ouvir", "bota", "coloca", "no spotify"]
            termo_limpo = cmd
            for g in gatilhos:
                termo_limpo = termo_limpo.replace(g, "")
            
            termo_limpo = termo_limpo.strip()
            
            if termo_limpo and len(termo_limpo) > 2:
                self.controller.play_search(termo_limpo)
                return f"Tentando tocar '{termo_limpo}' (Modo Instintivo)..."

        except Exception as e:
            logger.error(f"Erro no sistema límbico: {e}")
            return "Erro crítico no modo de emergência."

        return "Não compreendi o comando e a IA está offline."