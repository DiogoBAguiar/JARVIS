import json
import os
import re
from typing import Dict
from jarvis_system.cortex_frontal.observability import JarvisLogger

log = JarvisLogger("HIPOCAMPO_REFLEXOS")

class ReflexosMusculares:
    """
    Gerencia memória associativa rápida para correções fonéticas.
    Permite aprendizado em tempo real (Active Learning).
    """
    def __init__(self):
        # Caminho para o arquivo principal de configuração
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.config_path = os.path.join(self.base_dir, "data", "speech_config.json")
        self.phonetic_map: Dict[str, str] = {}
        self._carregar_memoria()

    def _carregar_memoria(self):
        """Lê o arquivo JSON para a RAM."""
        if not os.path.exists(self.config_path):
            self.phonetic_map = {}
            return

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                self.phonetic_map = dados.get("phonetic_map", {})
            log.info(f"🧠 {len(self.phonetic_map)} reflexos fonéticos carregados.")
        except Exception as e:
            log.error(f"Erro ao ler memória fonética: {e}")
            self.phonetic_map = {}

    def aprender(self, errado: str, correto: str) -> str:
        """
        Adiciona uma nova correção na memória RAM e no DISCO.
        Ex: aprender("tocasho", "tocar")
        """
        errado = errado.lower().strip()
        correto = correto.lower().strip()

        if errado == correto:
            return "Os termos são idênticos, não há o que aprender."

        # 1. Atualiza RAM (Instantâneo)
        self.phonetic_map[errado] = correto

        # 2. Atualiza DISCO (Persistência)
        try:
            # Lê o arquivo completo para não perder wake_words e known_apps
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    dados_completos = json.load(f)
            else:
                dados_completos = {}

            # Atualiza ou cria a seção phonetic_map
            dados_completos["phonetic_map"] = self.phonetic_map

            # Salva de volta
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(dados_completos, f, indent=4, ensure_ascii=False)
            
            log.info(f"✍️ Nova sinapse gravada: '{errado}' -> '{correto}'")
            return f"Aprendido. '{errado}' agora será entendido como '{correto}'."
        
        except Exception as e:
            log.error(f"Falha ao gravar aprendizado: {e}")
            return "Houve um erro ao tentar salvar essa memória."

    def corrigir(self, texto: str) -> str:
        """
        Aplica todas as correções conhecidas em um texto usando Regex.
        Isso garante que pontuação ou palavras compostas sejam tratadas corretamente.
        """
        if not self.phonetic_map: return texto
        
        texto_corrigido = texto.lower()
        
        # Ordena por tamanho (decrescente) para evitar que "apple watch" seja quebrado por "apple"
        mapa_ordenado = sorted(self.phonetic_map.items(), key=lambda x: len(x[0]), reverse=True)

        for erro, correcao in mapa_ordenado:
            if erro in texto_corrigido:
                # Regex Lookaround: Garante que só substitui a palavra inteira
                # Ex: Substitui "spot" mas não estraga "spotify"
                pattern = r'(?<!\w)' + re.escape(erro) + r'(?!\w)'
                texto_corrigido = re.sub(pattern, correcao, texto_corrigido)
        
        return texto_corrigido

# Instância Singleton exportada para uso no listen.py e orchestrator.py
reflexos = ReflexosMusculares()