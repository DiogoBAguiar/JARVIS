import os
import logging
import pdfkit
import markdown
import re
import requests # Necessário para baixar a imagem
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger("NEWS_REPORTER")

class NewsReporter:
    def __init__(self):
        # 1. Configurar Caminho do wkhtmltopdf
        possible_paths = [
            r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe",
            r"C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe",
            r"D:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe" 
        ]
        
        self.path_wkhtmltopdf = None
        for path in possible_paths:
            if os.path.exists(path):
                self.path_wkhtmltopdf = path
                break
        
        if self.path_wkhtmltopdf:
            self.config = pdfkit.configuration(wkhtmltopdf=self.path_wkhtmltopdf)
        else:
            logger.warning("⚠️ wkhtmltopdf não encontrado. O PDF não será gerado.")
            self.config = None

        # 2. Configurar Jinja2
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
        self.template_dir = os.path.join(base_path, "templates")
        self.img_cache_dir = os.path.join(base_path, "temp_images") # Pasta para imagens temporárias
        
        if not os.path.exists(self.img_cache_dir): os.makedirs(self.img_cache_dir)
        
        if os.path.exists(self.template_dir):
            self.env = Environment(loader=FileSystemLoader(self.template_dir))
        else:
            logger.error(f"❌ Pasta de templates não encontrada em: {self.template_dir}")

        self.output_folder = "relatorios_inteligencia"
        if not os.path.exists(self.output_folder): os.makedirs(self.output_folder)

    def _download_image(self, url):
        """Baixa a imagem da web para uma pasta local."""
        if not url: return None
        try:
            filename = f"img_{abs(hash(url))}.jpg"
            filepath = os.path.join(self.img_cache_dir, filename)
            
            # Se já baixou, retorna caminho formatado
            if os.path.exists(filepath): return self._format_path(filepath)

            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                return self._format_path(filepath)
        except Exception as e:
            logger.debug(f"⚠️ Falha ao baixar imagem: {e}")
        return None

    def _format_path(self, path):
        """Formata o caminho para o padrão file:/// que o wkhtmltopdf exige no Windows."""
        abs_path = os.path.abspath(path).replace("\\", "/")
        if os.name == 'nt':
            return f"file:///{abs_path}"
        return abs_path

    def _preparar_html_conteudo(self, markdown_text):
        text_clean = markdown_text.replace(r"\$", "$") 
        html = markdown.markdown(text_clean)
        html = re.sub(r'<p>', '<p class="drop-cap">', html, count=1)
        return html

    def criar_pdf(self, topico, texto_markdown, dados_brutos):
        logger.info(f"📄 Renderizando arquivo PDF sobre: {topico}...")

        try:
            conteudo_html = self._preparar_html_conteudo(texto_markdown)
            data_hoje = datetime.now().strftime("%d/%m/%Y")
            dia_semana = datetime.now().strftime("%A").upper()
            
            imagem_destaque = None
            galeria_imagens = []

            # --- LÓGICA HÍBRIDA: GALERIA vs DESTAQUE ÚNICO ---
            
            # 1. Detecta se é um tópico geral (ex: "Notícias do dia", "Resumo Geral")
            termos_gerais = ["notícias", "resumo", "briefing", "geral", "hoje", "dia", "manchetes", "principais"]
            eh_topico_geral = any(t in topico.lower() for t in termos_gerais) and len(topico.split()) < 6

            if eh_topico_geral:
                logger.info("📸 Modo Galeria ativado (Tópico Geral). Coletando imagens das notícias...")
                # Coleta até 4 imagens das notícias reais
                for item in dados_brutos:
                    if len(galeria_imagens) >= 4: break
                    
                    url_img = item.get('image')
                    if url_img:
                        caminho_local = self._download_image(url_img)
                        if caminho_local:
                            galeria_imagens.append({
                                "url": caminho_local,
                                "titulo": item.get('titulo', 'Notícia')
                            })
                
                # Se não achou imagens suficientes (min 2), desiste da galeria e tenta destaque único
                if len(galeria_imagens) < 2:
                    eh_topico_geral = False
                    galeria_imagens = []

            # 2. Modo Destaque Único (Se não for galeria)
            if not galeria_imagens:
                imagens_tematicas = {
                    "cripto": "https://images.unsplash.com/photo-1518546305927-5a555bb7020d?q=80&w=1000&auto=format&fit=crop",
                    "bitcoin": "https://images.unsplash.com/photo-1518546305927-5a555bb7020d?q=80&w=1000&auto=format&fit=crop",
                    "futebol": "https://images.unsplash.com/photo-1579952363873-27f3bade9f55?q=80&w=1000&auto=format&fit=crop",
                    "esporte": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?q=80&w=1000&auto=format&fit=crop",
                    "política": "https://images.unsplash.com/photo-1529101091760-61df6be5f18b?q=80&w=1000&auto=format&fit=crop",
                    "binance": "https://images.unsplash.com/photo-1621416894569-0f39ed31d247?q=80&w=1000&auto=format&fit=crop",
                    "dólar": "https://images.unsplash.com/photo-1580519542036-c47de6196ba5?q=80&w=1000&auto=format&fit=crop",
                    "games": "https://images.unsplash.com/photo-1552820728-8b83bb6b773f?q=80&w=1000&auto=format&fit=crop",
                    "tech": "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=1000&auto=format&fit=crop"
                }

                url_escolhida = None
                # Prioridade: Temática
                for chave, url in imagens_tematicas.items():
                    if chave in topico.lower():
                        url_escolhida = url
                        logger.info(f"🖼️ Usando imagem temática para: {chave}")
                        break
                
                # Fallback: RSS
                if not url_escolhida:
                    url_escolhida = next((item.get('image') for item in dados_brutos if item.get('image')), None)

                # Baixa a imagem
                caminho = self._download_image(url_escolhida)
                if caminho:
                    imagem_destaque = caminho

            # 3. Renderizar Template
            if not self.env: raise Exception("Ambiente Jinja2 falhou")
            template = self.env.get_template("newspaper.html")
            
            html_final = template.render(
                topico=topico,
                conteudo_html=conteudo_html,
                dados=dados_brutos,
                data_hoje=data_hoje,
                dia_semana=dia_semana,
                imagem_destaque=imagem_destaque,
                galeria_imagens=galeria_imagens # Passa a lista para o template
            )

            # 4. Configurações do PDF
            options = {
                'page-size': 'A4',
                'encoding': "UTF-8",
                'margin-top': '10mm',
                'margin-right': '10mm',
                'margin-bottom': '10mm',
                'margin-left': '10mm',
                'enable-local-file-access': "", 
                'no-outline': None,
                'zoom': 1.0
            }

            safe_title = topico.replace(" ", "_").replace("/", "-")
            filename = f"Jornal_{safe_title}_{datetime.now().strftime('%H%M%S')}.pdf"
            output_path = os.path.join(self.output_folder, filename)
            
            pdfkit.from_string(html_final, output_path, configuration=self.config, options=options)
            
            logger.info(f"✅ Arquivo PDF salvo: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"❌ Erro PDF: {e}")
            return None