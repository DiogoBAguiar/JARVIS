import os
import difflib
import glob
import webbrowser # <--- IMPORTANTE: Adicione isso no topo
from jarvis_system.cortex_frontal.observability import JarvisLogger

log = JarvisLogger("MOTOR_LAUNCHER")

class AppLauncher:
    def __init__(self):
        self.apps = {} 
        # Protocolos e Sites (Agora suporta URLs)
        self.uri_schemes = {
            "spotify": "spotify:",
            "whatsapp": "whatsapp:",
            "netflix": "netflix:",
            "calculadora": "calc",
            "steam": "steam://open/main",
            "discord": "discord:",
            "telegram": "tg://",
            
            # Sites úteis
            "chatgpt": "https://chatgpt.com",
            "gpt": "https://chatgpt.com",
            "youtube": "https://www.youtube.com",
            "google": "https://www.google.com",
            "github": "https://github.com",
            "gmail": "https://mail.google.com"
        }
        self._indexar_apps()

    def _indexar_apps(self):
        """Varre o Menu Iniciar para encontrar atalhos."""
        paths = [
            os.path.join(os.environ["ProgramData"], "Microsoft", "Windows", "Start Menu"),
            os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu")
        ]
        
        count = 0
        for root_path in paths:
            if not os.path.exists(root_path): continue
            for filepath in glob.glob(os.path.join(root_path, "**", "*.lnk"), recursive=True):
                filename = os.path.basename(filepath).lower()
                nome_app = filename.replace(".lnk", "").strip()
                self.apps[nome_app] = filepath
                count += 1
        
        log.info(f"Lançador indexado: {count} aplicativos locais encontrados.")

    def buscar_candidato(self, termo: str):
        termo = termo.lower().strip()
        
        # Remove espaços (ajuda em "chat gpt" -> "chatgpt")
        termo_clean = termo.replace(" ", "")

        # 1. Busca Exata
        if termo in self.uri_schemes: return "EXATO", termo, self.uri_schemes[termo]
        if termo_clean in self.uri_schemes: return "EXATO", termo_clean, self.uri_schemes[termo_clean]
        if termo in self.apps: return "EXATO", termo, self.apps[termo]

        # 2. Busca por Substring
        candidates_sub = [app for app in self.apps.keys() if termo in app]
        if candidates_sub:
            best_sub = min(candidates_sub, key=len)
            return "SUGESTAO", best_sub, self.apps[best_sub]

        # 3. Busca Fuzzy
        todas_opcoes = list(self.apps.keys()) + list(self.uri_schemes.keys())
        matches = difflib.get_close_matches(termo, todas_opcoes, n=1, cutoff=0.5)
        
        if matches:
            match = matches[0]
            caminho = self.apps.get(match) or self.uri_schemes.get(match)
            return "SUGESTAO", match, caminho
        
        return "NAO_ENCONTRADO", None, None

    def abrir_por_caminho(self, caminho: str):
        try:
            log.info(f"Executando: {caminho}")
            
            # Se for site (http/https), abre no navegador
            if caminho.startswith("http"):
                webbrowser.open(caminho)
            
            # Se for protocolo (spotify:) ou arquivo local, usa startfile
            else:
                os.startfile(caminho) 
            return True
        except Exception as e:
            log.error(f"Erro ao abrir {caminho}: {e}")
            return False

launcher = AppLauncher()