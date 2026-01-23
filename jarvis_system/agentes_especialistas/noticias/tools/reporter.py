import os
import requests
from fpdf import FPDF
from datetime import datetime
import textwrap

class PDFJornal(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        # --- O "Masthead" do Jornal ---
        self.set_font('Times', 'B', 24)
        # Cor Azul Escuro Profissional (Navy Blue)
        self.set_text_color(10, 25, 60)
        self.cell(0, 10, 'THE J.A.R.V.I.S. CHRONICLE', 0, 1, 'C')
        
        # Linha dupla estilo jornal antigo
        self.set_line_width(0.5)
        # Desenha linhas pretas para contraste
        self.set_draw_color(0, 0, 0)
        self.line(10, 22, 200, 22)
        self.line(10, 26, 200, 26)
        
        # --- AJUSTE DE DATA PT-BR MANUAL ---
        meses = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        agora = datetime.now()
        mes_nome = meses.get(agora.month)
        # Formato: 22 de Janeiro, 2026
        data_hoje = f"{agora.day} de {mes_nome}, {agora.year}"
        
        # Metadados (Data | Local | Edição)
        self.set_font('Arial', 'I', 9)
        self.set_text_color(100, 100, 100) # Cinza para subtítulo
        self.cell(0, 8, f"João Pessoa, PB  |  {data_hoje}  |  Edição de Inteligência Artificial", 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, label):
        self.set_font('Arial', 'B', 16)
        self.set_text_color(0, 0, 0) # Preto
        self.cell(0, 10, label, 0, 1, 'L')
        self.ln(2)

    def chapter_body(self, text):
        self.set_font('Times', '', 11)
        self.set_text_color(20, 20, 20)
        # Tratamento básico de encoding para evitar erros do FPDF com caracteres especiais
        texto_safe = text.encode('latin-1', 'replace').decode('latin-1')
        self.multi_cell(0, 6, texto_safe)
        self.ln()

class NewsReporter:
    def __init__(self):
        self.output_folder = "relatorios_inteligencia"
        self.img_cache = "temp_images"
        
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        if not os.path.exists(self.img_cache):
            os.makedirs(self.img_cache)

    def _download_image(self, url):
        """Tenta baixar imagem da notícia. Retorna path local ou None."""
        if not url: return None
        try:
            # User-Agent para evitar bloqueios simples
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=5, stream=True)
            if response.status_code == 200:
                # Cria nome único hash
                ext = url.split('.')[-1].split('?')[0] # Remove query params da extensão
                if len(ext) > 4 or len(ext) < 2: ext = "jpg"
                filename = f"{self.img_cache}/img_{abs(hash(url))}.{ext}"
                
                with open(filename, 'wb') as f:
                    f.write(response.content)
                return filename
        except Exception:
            return None
        return None

    def criar_pdf(self, titulo_topico, texto_analise, dados_brutos):
        pdf = PDFJornal()
        pdf.add_page()

        # --- MANCHETE PRINCIPAL ---
        pdf.set_font('Times', 'B', 20)
        pdf.set_text_color(190, 0, 0) # Vermelho "Breaking News"
        topico_safe = titulo_topico.upper().encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 10, topico_safe, align='C')
        pdf.ln(5)

        # --- IMAGEM DE DESTAQUE (Tenta pegar da primeira notícia) ---
        img_url = None
        # Procura a primeira imagem válida nos resultados
        for item in dados_brutos:
            if item.get('image'):
                img_url = item.get('image')
                break
        
        img_path = self._download_image(img_url)
        
        if img_path:
            try:
                # Centraliza imagem (largura 150)
                # O x=30 centraliza numa página A4 (210mm) -> (210-150)/2 = 30
                pdf.image(img_path, x=30, w=150) 
                pdf.ln(5)
            except:
                pass # Se a imagem for corrompida, ignora

        # --- CORPO DA MATÉRIA (Análise do LLM) ---
        pdf.ln(5)
        pdf.set_font('Times', '', 12)
        
        # Limpeza de Markdown do LLM
        clean_text = texto_analise.replace('**', '').replace('###', '').replace('##', '')
        pdf.chapter_body(clean_text)

        # --- RODAPÉ COM FONTES (Estilo "Classificados") ---
        pdf.ln(10)
        
        # Verifica se cabe na página, se não, cria nova
        if pdf.get_y() > 250:
            pdf.add_page()
            
        pdf.set_fill_color(240, 240, 240) # Fundo cinza claro
        # Desenha o fundo da caixa de fontes
        pdf.rect(10, pdf.get_y(), 190, 40, 'F') 
        
        pdf.set_y(pdf.get_y() + 5)
        pdf.set_font('Arial', 'B', 10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(10) # Indent
        pdf.cell(0, 8, "FONTES & REFERÊNCIAS:", 0, 1)
        
        pdf.set_font('Arial', '', 8)
        count = 0
        for item in dados_brutos:
            if count >= 4: break # Limita a 4 fontes para não estourar
            
            titulo = item.get('titulo', 'N/A')
            if len(titulo) > 80: titulo = titulo[:80] + "..."
            
            fonte = item.get('fonte', 'Web')
            link = item.get('link', '')
            if len(link) > 50: link = link[:50] + "..."
            
            line = f"• [{fonte}] {titulo} | {link}"
            safe_line = line.encode('latin-1', 'replace').decode('latin-1')
            
            pdf.cell(10) # Indent
            pdf.cell(0, 5, safe_line, 0, 1)
            count += 1

        # Salvar
        filename = f"{self.output_folder}/Jornal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf.output(filename)
        
        # Limpa imagens temporárias
        self._limpar_cache()
        
        return os.path.abspath(filename)

    def _limpar_cache(self):
        """Apaga as imagens baixadas para não lotar o disco."""
        if os.path.exists(self.img_cache):
            for f in os.listdir(self.img_cache):
                try:
                    os.remove(os.path.join(self.img_cache, f))
                except:
                    pass