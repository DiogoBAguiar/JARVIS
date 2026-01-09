import os
import re
import json
from jarvis_system.cortex_frontal.observability import JarvisLogger

# Tenta importar os reflexos para salvar o aprendizado
try:
    from jarvis_system.hipocampo.reflexos import reflexos
except ImportError:
    reflexos = None

class Dreamer:
    def __init__(self):
        self.log = JarvisLogger("SUBCONSCIENTE")
        self.base_dir = os.getcwd()
        # Ajuste o caminho conforme sua estrutura real de pastas de log
        self.log_file = os.path.join(self.base_dir, "logs", "jarvis_system.log")

    def processar_experiencias(self):
        """
        Lê o diário (logs) e transforma correções temporárias em sabedoria eterna.
        """
        if not os.path.exists(self.log_file):
            self.log.warning("Nenhum diário (log) encontrado para sonhar.")
            return

        self.log.info("💤 Entrando em estado de sonho (Processando logs)...")
        
        novos_conhecimentos = 0
        padroes_encontrados = set()

        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                linhas = f.readlines()

            # Padrão que criamos no agente_spotify.py
            # Ex: [NLU] Correção LLM: 'frigilson' -> 'Frei Gilson'
            regex_correcao = r"Correção LLM: '(.+?)' -> '(.+?)'"

            for linha in linhas:
                match = re.search(regex_correcao, linha)
                if match:
                    erro_fonetico = match.group(1).lower().strip()
                    correcao_real = match.group(2).strip()
                    
                    # Evita aprender o óbvio (se for igual)
                    if erro_fonetico == correcao_real.lower():
                        continue

                    # Adiciona ao set para evitar duplicatas no mesmo ciclo
                    padroes_encontrados.add((erro_fonetico, correcao_real))

            # Consolidação na Memória
            if reflexos:
                for erro, correcao in padroes_encontrados:
                    # O método aprender do reflexos deve salvar no JSON
                    sucesso = reflexos.aprender(erro, correcao)
                    if sucesso:
                        self.log.info(f"💡 Aprendi: '{erro}' agora é '{correcao}'")
                        novos_conhecimentos += 1
            
            if novos_conhecimentos > 0:
                self.log.info(f"✨ Sonho concluído. {novos_conhecimentos} novas sinapses criadas.")
            else:
                self.log.info("💤 Nada novo para aprender hoje.")

            # Opcional: Arquivar o log antigo para não reprocessar eternamente
            # self._arquivar_logs()

        except Exception as e:
            self.log.error(f"Pesadelo (Erro ao processar logs): {e}")

    def _arquivar_logs(self):
        # Implementação futura: mover jarvis_system.log para logs/archive/data.log
        pass

# Instância para uso
dreamer = Dreamer()

if __name__ == "__main__":
    dreamer.processar_experiencias()