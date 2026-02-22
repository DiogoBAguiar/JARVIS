import os
import json
import glob
import difflib
import webbrowser
from abc import ABC, abstractmethod

from jarvis_system.cortex_frontal.observability import JarvisLogger

logger = JarvisLogger("MOTOR_LAUNCHER")

class ArmazenamentoBase(ABC):
    """Abstração para o repositório de dados do lançador."""
    @abstractmethod
    def carregar(self) -> dict: pass
    
    @abstractmethod
    def salvar(self, dados: dict): pass

class ArmazenamentoJSON(ArmazenamentoBase):
    """Implementação concreta de armazenamento persistente em arquivo JSON."""
    def __init__(self, caminho_arquivo: str):
        self.caminho_arquivo = caminho_arquivo

    def carregar(self) -> dict:
        if not os.path.exists(self.caminho_arquivo):
            return {}
        try:
            with open(self.caminho_arquivo, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as erro:
            logger.error(f"Erro ao ler cache JSON: {erro}")
            return {}

    def salvar(self, dados: dict):
        try:
            with open(self.caminho_arquivo, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=4, ensure_ascii=False)
        except Exception as erro:
            logger.error(f"Erro ao salvar cache JSON: {erro}")

class LancadorDeAplicativos:
    """
    Motor centralizado de inicialização de processos.
    Utiliza composição para persistência e busca difusa (Fuzzy) para tolerância a erros.
    """
    def __init__(self, armazenamento: ArmazenamentoBase):
        self.armazenamento = armazenamento
        self.aplicativos = {}
        
        # Esquemas base e URIs
        self.esquemas_uri = {
            "spotify": "spotify:",
            "whatsapp": "whatsapp:",
            "netflix": "netflix:",
            "calculadora": "calc",
            "bloco de notas": "notepad",
            "steam": "steam://open/main",
            "discord": "discord:",
            "chatgpt": "https://chatgpt.com",
            "youtube": "https://www.youtube.com",
            "github": "https://github.com"
        }
        
        self._inicializar_indice()

    def _inicializar_indice(self):
        """Carrega do JSON. Se estiver vazio, realiza a varredura inicial (Cold Start)."""
        self.aplicativos = self.armazenamento.carregar()
        
        if not self.aplicativos:
            logger.info("Índice JSON vazio. Reconstruindo através da varredura do Windows...")
            self.reconstruir_indice()
        else:
            logger.info(f"Índice carregado do JSON com {len(self.aplicativos)} aplicativos locais.")

    def reconstruir_indice(self):
        """Varre o sistema e atualiza o arquivo JSON mestre."""
        caminhos_busca = [
            os.path.join(os.environ.get("ProgramData", "C:\\ProgramData"), "Microsoft", "Windows", "Start Menu"),
            os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu")
        ]
        
        novo_indice = {}
        contagem = 0
        for caminho_raiz in caminhos_busca:
            if not os.path.exists(caminho_raiz):
                continue
            for caminho_arquivo in glob.glob(os.path.join(caminho_raiz, "**", "*.lnk"), recursive=True):
                nome_arquivo = os.path.basename(caminho_arquivo).lower()
                nome_limpo = nome_arquivo.replace(".lnk", "").strip()
                novo_indice[nome_limpo] = os.path.abspath(caminho_arquivo)
                contagem += 1
        
        self.aplicativos = novo_indice
        self.armazenamento.salvar(self.aplicativos)
        logger.info(f"Índice reconstruído e salvo: {contagem} aplicativos indexados no JSON.")

    def buscar_candidato(self, termo: str) -> tuple[str, str, str]:
        """
        Pesquisa o termo usando correspondência exata ou aproximada (Fuzzy Matching).
        Retorna: (Status, Nome_Encontrado, Caminho_Absoluto)
        """
        termo = termo.lower().strip()
        termo_limpo = termo.replace(" ", "")

        # 1. Busca Exata Rápida (O(1))
        if termo in self.esquemas_uri: return "EXATO", termo, self.esquemas_uri[termo]
        if termo_limpo in self.esquemas_uri: return "EXATO", termo_limpo, self.esquemas_uri[termo_limpo]
        if termo in self.aplicativos: return "EXATO", termo, self.aplicativos[termo]

        # 2. Busca por Substring Distribuída (O(n))
        candidatos_sub = [app for app in self.aplicativos.keys() if termo in app]
        if candidatos_sub:
            melhor_sub = min(candidatos_sub, key=len)
            return "SUGESTAO", melhor_sub, self.aplicativos[melhor_sub]

        # 3. Busca Fuzzy / Distância de Levenshtein
        todas_opcoes = list(self.aplicativos.keys()) + list(self.esquemas_uri.keys())
        correspondencias = difflib.get_close_matches(termo, todas_opcoes, n=1, cutoff=0.5)
        
        if correspondencias:
            melhor_correspondencia = correspondencias[0]
            caminho_alvo = self.aplicativos.get(melhor_correspondencia) or self.esquemas_uri.get(melhor_correspondencia)
            return "SUGESTAO", melhor_correspondencia, caminho_alvo
        
        return "NAO_ENCONTRADO", "", ""

    def abrir_por_caminho(self, caminho: str) -> bool:
        """Invoca o sistema operacional para executar o arquivo ou URL."""
        try:
            logger.info(f"Executando caminho absoluto/URI: {caminho}")
            if caminho.startswith("http"):
                webbrowser.open(caminho)
            else:
                os.startfile(caminho) 
            return True
        except Exception as erro:
            logger.error(f"Falha de execução no SO para {caminho}: {erro}")
            return False

# Injeção de Dependências e Instanciação (Singleton)
# O arquivo JSON será criado na mesma pasta deste script
caminho_banco_dados = os.path.join(os.path.dirname(os.path.abspath(__file__)), "indice_aplicativos.json")
estrategia_armazenamento = ArmazenamentoJSON(caminho_banco_dados)

# Variável exportada para o sistema (Mantenha o nome 'launcher' se já o usa em outros módulos)
launcher = LancadorDeAplicativos(estrategia_armazenamento)