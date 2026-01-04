import os
import difflib
import glob
from jarvis_system.cortex_frontal.observability import JarvisLogger

log = JarvisLogger("MOTOR_LAUNCHER")

class AppLauncher:
    def __init__(self):
        self.apps = {} 
        # Mantemos apenas os essenciais de protocolo/caminho, sem correções fonéticas malucas
        self.uri_schemes = {
            "spotify": "spotify:",
            "whatsapp": "whatsapp:",
            "netflix": "netflix:",
            "calculadora": "calc",
            "steam": "steam://open/main"
        }
        self._indexar_apps()

    def _indexar_apps(self):
        paths = [
            os.path.join(os.environ["ProgramData"], "Microsoft", "Windows", "Start Menu"),
            os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu")
        ]
        for root_path in paths:
            if not os.path.exists(root_path): continue
            for filepath in glob.glob(os.path.join(root_path, "**", "*.lnk"), recursive=True):
                filename = os.path.basename(filepath).lower()
                nome_app = filename.replace(".lnk", "").strip()
                self.apps[nome_app] = filepath

    def buscar_candidato(self, termo: str):
        """
        Retorna: (status, nome_real, caminho_ou_uri)
        status: 'EXATO', 'SUGESTAO', 'NAO_ENCONTRADO'
        """
        termo = termo.lower().strip()

        # 1. Busca Exata (Prioridade Máxima)
        if termo in self.uri_schemes:
            return "EXATO", termo, self.uri_schemes[termo]
        if termo in self.apps:
            return "EXATO", termo, self.apps[termo]

        # 2. Busca Aproximada (Fuzzy)
        # Combina chaves dos apps e dos protocolos
        todas_opcoes = list(self.apps.keys()) + list(self.uri_schemes.keys())
        
        # Procura algo com pelo menos 40% de semelhança (cutoff=0.4)
        # Isso permite achar 'visual studio' a partir de 'olhos estúdio' (por causa do 'estúdio')
        matches = difflib.get_close_matches(termo, todas_opcoes, n=1, cutoff=0.4)
        
        if matches:
            match = matches[0]
            # Recupera o caminho
            caminho = self.apps.get(match) or self.uri_schemes.get(match)
            return "SUGESTAO", match, caminho
        
        return "NAO_ENCONTRADO", None, None

    def abrir_por_caminho(self, caminho: str):
        try:
            if ":" in caminho and not "\\" in caminho and not "/" in caminho:
                os.system(f"start {caminho}") # É protocolo (spotify:)
            else:
                os.startfile(caminho) # É arquivo (.lnk)
            return True
        except Exception:
            return False

launcher = AppLauncher()