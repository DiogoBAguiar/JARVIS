import os
import requests
from fpdf import FPDF
from datetime import datetime
import textwrap

# --- PALETA DE CORES (DESIGN SYSTEM) ---
COLOR_PRIMARY = (10, 25, 60)    # Navy Blue
COLOR_ACCENT = (180, 0, 0)      # Vermelho
COLOR_TEXT = (20, 20, 20)       # Preto Suave
COLOR_GRAY = (100, 100, 100)    # Cinza
COLOR_BG_BOX = (240, 245, 250)  # Azul Gelo

class PDFJornal(FPDF):
    def __init__(self):
        super().__init__()
        self.set_margins(20, 20, 20)
        self.set_auto_page_break(auto=True, margin=20)

    def _sanitizar(self, text):
        """
        Converte caracteres Unicode complexos para Latin-1 seguro.
        Evita o crash '\u2022'.
        """
        if not text: return ""
        # Mapa de substituição manual para caracteres comuns que o LLM usa
        replacements = {
            '\u2022': '-',  # Bullet point •
            '\u2013': '-',  # En dash –
            '\u2014': '-',  # Em dash —
            '\u2018': "'",  # Left single quote
            '\u2019': "'",  # Right single quote
            '\u201c': '"',  # Left double quote “
            '\u201d': '"',  # Right double quote ”
            '\u2026': '...', # Ellipsis …
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        # Codificação final de segurança (substitui o que sobrar por ?)
        return text.encode('latin-1', 'replace').decode('latin-1')

    def header(self):
        # 1. Título
        self.set_font('Times', 'B', 26)
        self.set_text_color(*COLOR_PRIMARY)
        self.cell(0, 12, 'THE J.A.R.V.I.S. CHRONICLE', 0, 1, 'C')
        
        # 2. Linhas
        self.set_draw_color(50, 50, 50)
        self.set_line_width(0.3)
        y_line = self.get_y() + 2
        self.line(20, y_line, 190, y_line)
        self.line(20, y_line + 1.5, 190, y_line + 1.5)
        
        # 3. Metadados
        self.ln(5)
        meses = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 
                 7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
        agora = datetime.now()
        data_extenso = f"{agora.day} de {meses.get(agora.month)}, {agora.year}"
        
        self.set_font('Arial', 'B', 8)
        self.set_text_color(*COLOR_GRAY)
        # Usei PIPE (|) em vez de bullet (•) para evitar crash
        meta_text = f"JOAO PESSOA, PB   |   {data_extenso.upper()}   |   INTELLIGENCE BRIEFING"
        self.cell(0, 6, self._sanitizar(meta_text), 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(150, 150, 150)
        # Rodapé seguro
        texto = f'J.A.R.V.I.S. AI System | Pagina {self.page_no()}'
        self.cell(0, 10, self._sanitizar(texto), 0, 0, 'C')

    def draw_lead_paragraph(self, text):
        self.set_font('Times', 'B', 12)
        self.set_text_color(*COLOR_TEXT)
        self.multi_cell(0, 6, self._sanitizar(text))
        self.ln(5)

    def draw_body_paragraph(self, text):
        self.set_font('Times', '', 11)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 6, self._sanitizar(text))
        self.ln(3)

    def draw_insight_box(self, text):
        self.ln(5)
        self.set_fill_color(*COLOR_BG_BOX)
        self.set_draw_color(*COLOR_PRIMARY)
        self.set_line_width(0.5)
        
        y_start = self.get_y()
        self.set_font('Arial', 'I', 10)
        self.set_text_color(*COLOR_PRIMARY)
        
        # Hack para simular padding: desenha texto recuado
        x_orig = self.get_x()
        self.set_x(x_orig + 4)
        self.multi_cell(160, 6, self._sanitizar(text))
        self.set_x(x_orig) # Volta X
        
        # Desenha a linha lateral azul (Quote style)
        y_end = self.get_y()
        self.set_draw_color(*COLOR_PRIMARY)
        self.set_line_width(1.5)
        self.line(22, y_start + 1, 22, y_end - 1)
        self.ln(5)

class NewsReporter:
    def __init__(self):
        self.output_folder = "relatorios_inteligencia"
        self.img_cache = "temp_images"
        if not os.path.exists(self.output_folder): os.makedirs(self.output_folder)
        if not os.path.exists(self.img_cache): os.makedirs(self.img_cache)

    def _download_image(self, url):
        if not url: return None
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=5, stream=True)
            if response.status_code == 200:
                ext = url.split('.')[-1].split('?')[0]
                if len(ext) > 4 or len(ext) < 2: ext = "jpg"
                filename = f"{self.img_cache}/img_{abs(hash(url))}.{ext}"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                return filename
        except:
            return None
        return None

    def criar_pdf(self, titulo_topico, texto_analise, dados_brutos):
        try:
            pdf = PDFJornal()
            pdf.add_page()

            # 1. MANCHETE
            pdf.set_font('Times', 'B', 24)
            pdf.set_text_color(*COLOR_ACCENT)
            topico_safe = pdf._sanitizar(titulo_topico.upper())
            pdf.multi_cell(0, 10, topico_safe, align='C')
            pdf.ln(8)

            # 2. IMAGEM
            img_url = next((item.get('image') for item in dados_brutos if item.get('image')), None)
            img_path = self._download_image(img_url)
            
            if img_path:
                try:
                    x_pos = 30
                    width = 150
                    pdf.image(img_path, x=x_pos, w=width)
                    # Borda fina
                    pdf.set_draw_color(200, 200, 200)
                    pdf.set_line_width(0.2)
                    y_img = pdf.get_y()
                    # Legenda
                    pdf.ln(2)
                    pdf.set_font('Arial', '', 7)
                    pdf.set_text_color(150, 150, 150)
                    pdf.cell(0, 4, "Imagem recuperada via Web/RSS - Fonte ilustrativa", 0, 1, 'C')
                    pdf.ln(8)
                except: pass

            # 3. CORPO
            clean_text = texto_analise.replace('**', '').replace('###', '').replace('##', '')
            paragrafos = clean_text.split('\n')
            paragrafos = [p for p in paragrafos if len(p.strip()) > 5]
            
            if paragrafos:
                pdf.draw_lead_paragraph(paragrafos[0])
                for p in paragrafos[1:]:
                    if "Conclusão" in p or "Em resumo" in p or "Análise:" in p:
                        pdf.draw_insight_box(p)
                    else:
                        pdf.draw_body_paragraph(p)

            # 4. FONTES
            pdf.ln(10)
            if pdf.get_y() > 240: pdf.add_page()
            
            pdf.set_fill_color(245, 245, 245)
            pdf.set_font('Arial', 'B', 9)
            pdf.set_text_color(*COLOR_PRIMARY)
            pdf.cell(0, 8, "FONTES VERIFICADAS:", 0, 1, 'L', fill=True)
            
            pdf.set_font('Arial', '', 8)
            pdf.set_text_color(50, 50, 50)
            
            count = 0
            for item in dados_brutos:
                if count >= 5: break
                titulo = item.get('titulo', 'N/A')[:90].replace('\n', ' ')
                fonte = item.get('fonte', 'Web')
                
                # Sanitização manual aqui também
                safe_line = pdf._sanitizar(f"[{fonte}] {titulo}")
                
                pdf.set_x(25)
                pdf.cell(5, 5, ">>", 0, 0)
                pdf.cell(0, 5, safe_line, 0, 1)
                count += 1

            # SALVAR
            filename = f"{self.output_folder}/Relatorio_Jarvis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf.output(filename)
            
            return os.path.abspath(filename)
            
        finally:
            # Garante limpeza mesmo se der erro
            self._limpar_cache()

    def _limpar_cache(self):
        if os.path.exists(self.img_cache):
            for f in os.listdir(self.img_cache):
                try: os.remove(os.path.join(self.img_cache, f))
                except: pass