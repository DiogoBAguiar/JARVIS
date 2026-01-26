import os
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

# 1. Configuração dos Caminhos
# Ajuste este caminho para apontar para a pasta onde está o seu newspaper.html
TEMPLATE_DIR = 'D:/projetos/J.A.R.V.I.S/jarvis_system/agentes_especialistas/noticias/templates'

OUTPUT_FILE = 'teste_renderizado_massivo.html'

# --- CSS HARDCODED ---
CSS_PREMIUM = """
/* --- CONFIGURAÇÕES VISUAIS PREMIUM --- */
:root {
  --bg-paper: #f4f1ea;
  --ink-black: #1a1a1a;
  --accent-red: #8a1c1c;
  --page-width: 210mm;
  --page-height: 297mm;
  --margin-top: 15mm;
  --margin-side: 18mm; 
  --margin-bottom: 12mm; 
  --footer-height: 8mm; 
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  background: #2e2e2e;
  font-family: 'Lora', serif;
  color: var(--ink-black);
  padding: 40px;
  -webkit-font-smoothing: antialiased;
}

/* --- PÁGINA --- */
.page {
  width: var(--page-width);
  height: var(--page-height);
  background-color: var(--bg-paper);
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.05'/%3E%3C/svg%3E");
  margin: 0 auto 40px auto;
  position: relative;
  box-shadow: 0 1px 1px rgba(0,0,0,0.15), 0 10px 0 -5px #eee, 0 30px 30px rgba(0,0,0,0.3);
  display: flex;
  flex-direction: column;
  padding: var(--margin-top) var(--margin-side) var(--margin-bottom) var(--margin-side);
  border: 1px solid #d3cfc6;
}

.content-area {
  width: 100%;
  height: calc(100% - var(--footer-height)); 
  overflow: hidden; 
  display: flex;
  flex-direction: column;
}

.page-footer {
  height: var(--footer-height);
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid var(--ink-black);
  border-bottom: 1px solid var(--ink-black);
  margin-top: auto; 
  padding-top: 2px;
  font-family: 'Cinzel', serif;
  font-size: 7pt;
  letter-spacing: 1px;
  font-weight: 700;
  color: #444;
}

#source-content { display: none; }

/* --- CABEÇALHO --- */
.header-section { text-align: center; border-bottom: 4px double var(--ink-black); padding-bottom: 15px; margin-bottom: 25px; flex-shrink: 0; }
.meta-header { display: flex; justify-content: space-between; font-family: sans-serif; font-size: 7pt; font-weight: 800; text-transform: uppercase; letter-spacing: 2px; border-bottom: 1px solid var(--ink-black); padding-bottom: 6px; margin-bottom: 12px; color: #555; }
.main-title { font-family: 'Cinzel', serif; font-size: 46pt; font-weight: 900; letter-spacing: -1px; margin: 10px 0 5px 0; line-height: 0.9; text-transform: uppercase; text-shadow: 1px 1px 0px rgba(0,0,0,0.1); }
.motto { font-family: 'Playfair Display', serif; font-style: italic; font-size: 11pt; margin-bottom: 15px; color: #444; }
.info-bar { border-top: 1px solid var(--ink-black); border-bottom: 1px solid var(--ink-black); padding: 6px; font-size: 8pt; font-weight: bold; text-transform: uppercase; letter-spacing: 3px; background-color: rgba(0,0,0,0.03); }

/* --- MANCHETE E GRID --- */
.headline-section { text-align: center; margin-bottom: 35px; flex-shrink: 0; }
.headline-section h2 { font-family: 'Playfair Display', serif; font-size: 32pt; font-weight: 900; text-transform: uppercase; line-height: 1; margin-bottom: 10px; }
.headline-section p { font-family: 'Lora', serif; font-size: 12pt; font-style: italic; color: var(--accent-red); }

.dashboard-grid { display: grid; grid-template-columns: 1fr 1px 2.5fr 1px 1fr; gap: 15px; align-content: start; }
.vertical-line { background-color: #ccc; width: 1px; height: 100%; }

.sidebar h3 { font-family: 'Cinzel', serif; font-size: 9pt; border-bottom: 2px solid var(--ink-black); margin-bottom: 12px; font-weight: 900; text-transform: uppercase; letter-spacing: 1px; }
.sidebar-item { margin-bottom: 10px; border-bottom: 1px dotted #999; padding-bottom: 6px; font-size: 8.5pt; line-height: 1.3; }
.sidebar-item strong { display: block; color: var(--accent-red); font-size: 7.5pt; text-transform: uppercase; }

.gallery { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px; }
.gallery img { width: 100%; height: 90px; object-fit: cover; border: 1px solid #333; filter: grayscale(100%) contrast(120%) sepia(20%); display: block; }
.caption { font-family: sans-serif; font-size: 6pt; text-transform: uppercase; margin-top: 3px; text-align: right; color: #666; }

.summary-box { border-top: 1px solid var(--ink-black); border-bottom: 1px solid var(--ink-black); padding: 10px 0; font-size: 10.5pt; text-align: justify; font-style: italic; line-height: 1.5; }

/* --- MIOLO --- */
.text-block { font-family: 'Merriweather', serif; font-size: 10.5pt; line-height: 1.65; text-align: justify; margin-bottom: 18px; color: #222; hyphens: auto; }
.text-block h3 { font-family: 'Cinzel', serif; font-size: 14pt; font-weight: 700; color: var(--ink-black); border-bottom: 2px solid var(--accent-red); padding-bottom: 5px; margin: 30px 0 15px 0; text-transform: uppercase; letter-spacing: 1px; text-align: center; }
.text-block ul { list-style: none; padding: 15px 0; margin: 15px 15px; border-top: 1px solid #ddd; border-bottom: 1px solid #ddd; }
.text-block li { margin-bottom: 6px; padding-left: 20px; position: relative; font-size: 10pt; font-style: italic; color: #444; }
.text-block li::before { content: "❧"; position: absolute; left: 0; color: var(--accent-red); font-size: 10pt; }

/* DROP CAP (CSS) - Ajustado */
.drop-cap { float: left; font-family: 'Cinzel', serif; font-size: 55pt; line-height: 0.8; padding-right: 12px; padding-top: 2px; color: var(--ink-black); text-shadow: 2px 2px 0px rgba(0,0,0,0.1); }

@media print {
  body { background: none; margin: 0; padding: 0; }
  .page { margin: 0; box-shadow: none; border: none; background: white; break-after: page; page-break-after: always; }
  @page { size: A4; margin: 0; }
}
"""

def renderizar_teste():
    if not os.path.exists(TEMPLATE_DIR):
        print(f"ERRO: Diretório de templates não encontrado em: {TEMPLATE_DIR}")
        print("Ajuste a variável TEMPLATE_DIR no script.")
        return

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    try:
        template = env.get_template('newspaper.html')
    except Exception as e:
        print(f"Erro ao carregar o template newspaper.html: {e}")
        return

    # --- DADOS MOCK ---
    lista_fontes = []
    nomes_fontes = ["TechCrunch", "The Verge", "Wired", "MIT Review", "Estadão", "Folha", "Reuters", "CNN", "BBC", "Al Jazeera"]
    
    for i in range(1, 61):
        fonte_base = nomes_fontes[i % len(nomes_fontes)]
        lista_fontes.append({
            "fonte": f"{fonte_base} #{i}", 
            "titulo": f"Manchete de teste de carga número {i} sobre sistemas distribuídos e concorrência", 
            "link": "#"
        })

    lista_imagens = [
        {"url": f"https://picsum.photos/400/300?random={i}", "titulo": f"Evidência Visual #{i}"}
        for i in range(1, 21)
    ]

    # --- CORREÇÃO AQUI (Ajuste da Drop Cap no conteúdo) ---
    # Usamos <span> dentro do <p>, e não quebramos o parágrafo
    conteudo_massivo = """
    <p><span class="drop-cap">E</span>ste relatório representa um teste de estresse extremo para a interface do J.A.R.V.I.S. Chronicle. O objetivo é validar o comportamento das colunas laterais (sidebars) e a legibilidade tipográfica quando submetidas a uma carga de informação muito superior ao padrão habitual de um briefing diário.</p>
    """
    
    for i in range(1, 16):
        conteudo_massivo += f"""
        <h3>Seção de Análise Profunda #{i}</h3>
        <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. A densidade da informação aqui apresentada visa simular um relatório técnico completo gerado pelo Agente Especialista.</p>
        
        <p>Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
        
        <ul>
            <li>Ponto de dados crítico verificado na iteração {i}.A</li>
            <li>Anomalia detectada no subsistema de renderização {i}.B</li>
            <li>Latência de resposta aumentada em {i * 10}ms</li>
        </ul>
        """

    dados_mock = {
        "data_hoje": datetime.now().strftime("%d/%m/%Y"),
        "dia_semana": "SÁBADO (CARGA MÁXIMA)",
        "topico": "Relatório de Stress Test & Layout",
        "resumo_executivo": "Este teste valida a integridade visual do sistema J.A.R.V.I.S., garantindo que a injeção direta de CSS via Python mantenha o design premium mesmo sem arquivos externos.",
        "dados": lista_fontes,
        "conteudo_html": conteudo_massivo,
        "css_conteudo": CSS_PREMIUM,
        "galeria_imagens": lista_imagens, 
        "imagem_destaque": "https://picsum.photos/800/400?grayscale"
    }

    try:
        html_saida = template.render(**dados_mock)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(html_saida)

        print(f"✅ Sucesso! Abra o arquivo '{OUTPUT_FILE}' no navegador.")
        print(f"   - Fontes geradas: {len(lista_fontes)}")
        print(f"   - Imagens geradas: {len(lista_imagens)}")
        print(f"   - CSS Injetado (Hardcoded): Sim ({len(CSS_PREMIUM)} caracteres)")

    except Exception as e:
        print(f"❌ Erro durante a renderização: {e}")

if __name__ == "__main__":
    renderizar_teste()