import logging
import json
import os
import re
from urllib.parse import urlparse
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# --- IMPORTAÇÃO DO PLAYWRIGHT ---
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

from ..tools.search_engine import NewsEngine

# --- IMPORTAÇÃO DOS PROMPTS ---
try:
    from . import prompts
except ImportError:
    prompts = None 

# Dependências Opcionais
try:
    from .classifier import IntentRouter
except ImportError:
    IntentRouter = None 

try:
    from .llm_setup_noticias import LLMFactory, SafeAgent, MockAgent
    from agno.agent import Agent
except ImportError:
    LLMFactory = None
    Agent = None
    SafeAgent = None
    MockAgent = None

logger = logging.getLogger("NEWS_BRAIN_JARVIS")

class NewsBrain:
    def __init__(self):
        self.engine = NewsEngine()
        self.agent_llm = None
        
        # Caminhos
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.template_dir = os.path.join(self.base_dir, "..", "templates")
        
        if not sync_playwright:
            logger.warning("⚠️ Playwright não instalado. Rode: pip install playwright && playwright install chromium")

        if IntentRouter:
            self.router = IntentRouter()
        else:
            self.router = None
        self._setup_analyst()

    def _setup_analyst(self):
        if LLMFactory and Agent and SafeAgent:
            model = LLMFactory.get_model("llama-3.3-70b-versatile")
            if model:
                real_agent = Agent(model=model, description="Analista J.A.R.V.I.S.", markdown=False)
                self.agent_llm = SafeAgent(real_agent)
            else:
                self.agent_llm = MockAgent()
        elif MockAgent:
             self.agent_llm = MockAgent()

    def processar_solicitacao(self, user_input: str) -> str:
        if not self.router: return "Erro Crítico: Router ausente."
        logger.info(f"🧠 Analisando intenção: '{user_input}'...")
        
        plano = self.router.classificar(user_input)
        if not plano: plano = {}
        
        intent = plano.get("intent", "investigacao")
        complexity = plano.get("complexity", "low")
        topico = plano.get("topic", user_input)
        
        logger.info(f"📋 Plano: {intent} | Complexidade: {complexity}")

        dados_coletados = self._executar_coleta(plano, user_input)

        if not dados_coletados:
             is_mock = False
             try:
                 if isinstance(self.agent_llm, MockAgent): is_mock = True
                 if hasattr(self.agent_llm, 'mock') and self.agent_llm.agent is None: is_mock = True
             except: pass
             
             if not is_mock and "simulacao" not in topico.lower():
                 return f"Senhor, busquei informações sobre '{topico}', mas minhas fontes não retornaram dados satisfatórios."

        gerar_jornal = (intent == "analise") or (complexity == "high") or ("relatório" in user_input.lower()) or ("jornal" in user_input.lower()) or ("novidades" in user_input.lower())
        
        if gerar_jornal:
            return self._gerar_jornal_completo(topico, dados_coletados)
        else:
            return self._fluxo_apenas_voz(topico, intent, dados_coletados)

    def _executar_coleta(self, plano, user_input_fallback=""):
        dados = []
        fontes = plano.get("recommended_sources", [])
        topico = plano.get("topic", user_input_fallback)
        intent_val = plano.get('intent', 'investigacao')
        
        if "web_search" in fontes or intent_val in ["investigacao", "analise", "historia"]:
            termo = plano.get("search_term", topico)
            logger.info(f"🌍 Busca Web: '{termo}'")
            dados += self.engine.search_topic(termo)
            
        for fonte in fontes:
            if "rss_" in fonte:
                cat = fonte.replace("rss_", "")
                logger.info(f"📡 RSS: {cat}")
                dados += self.engine.get_briefing(categoria=cat, limit=3)
        return dados

    def _gerar_jornal_completo(self, topico, dados):
        logger.info("📰 Editorando J.A.R.V.I.S. Chronicle...")
        if not self.agent_llm or not prompts: return "Erro: IA indisponível."

        # 1. LLM gera JSON
        prompt_jornal = prompts.get_newspaper_json_prompt(topico, json.dumps(dados, ensure_ascii=False))
        resp_obj = self.agent_llm.run(prompt_jornal)
        texto_resp = resp_obj.content if hasattr(resp_obj, 'content') else str(resp_obj)
        
        # 2. Parse JSON
        try:
            match = re.search(r'\{.*\}', texto_resp, re.DOTALL)
            if match:
                clean_json = match.group(0)
                conteudo_estruturado = json.loads(clean_json)
            else:
                clean_json = texto_resp.replace("```json", "").replace("```", "").strip()
                conteudo_estruturado = json.loads(clean_json)
        except Exception as e:
            logger.error(f"Erro JSON: {e}")
            conteudo_estruturado = {
                "resumo_executivo": "Não foi possível estruturar o resumo.",
                "conteudo_html": f"<p>{texto_resp}</p>"
            }

        # 3. Tratamento de Fontes
        dados_processados = []
        for d in dados:
            link = d.get('url') or d.get('href') or d.get('link') or ''
            
            titulo = d.get('title') or d.get('header') or d.get('body') or d.get('snippet')
            if not titulo and link: titulo = link
            elif not titulo: titulo = "Informação da Web"

            titulo = str(titulo).replace('\n', ' ').strip()
            if len(titulo) > 85: titulo = titulo[:82] + "..."

            fonte_nome = d.get('source') or d.get('domain') or d.get('name') or d.get('site_name')
            
            if not fonte_nome and link:
                try:
                    parsed = urlparse(link)
                    fonte_nome = parsed.netloc.replace('www.', '').split('.')[0].upper()
                except:
                    fonte_nome = 'WEB'
            
            if not fonte_nome: fonte_nome = 'WEB'

            dados_processados.append({
                "fonte": str(fonte_nome).upper(),
                "titulo": titulo,
                "url": link 
            })

        # 4. Imagens
        galeria = []
        for d in dados:
            img_url = d.get('image') or d.get('img') or d.get('thumbnail')
            if img_url:
                galeria.append({"url": img_url, "titulo": "Imagem da Fonte"})
        
        if not galeria:
            galeria = [
                {"url": "https://picsum.photos/400/300?grayscale&random=1", "titulo": "Arquivo J.A.R.V.I.S."},
                {"url": "https://picsum.photos/400/300?grayscale&random=2", "titulo": "Dados de Rede"}
            ]

        # 5. Renderização HTML
        try:
            env = Environment(loader=FileSystemLoader(self.template_dir))
            template = env.get_template('newspaper.html')
            
            contexto = {
                "topico": topico.title(),
                "data_hoje": datetime.now().strftime("%d/%m/%Y"),
                "dia_semana": datetime.now().strftime("%A").upper(),
                "resumo_executivo": conteudo_estruturado.get("resumo_executivo", ""),
                "conteudo_html": conteudo_estruturado.get("conteudo_html", ""),
                "dados": dados_processados, 
                "galeria_imagens": galeria[:4],
                "imagem_destaque": "https://picsum.photos/800/400?grayscale",
                "nome_agente": "J.A.R.V.I.S. Intel v1.0", # Nome dinâmico para o HTML
                "css_conteudo": "" 
            }
            
            html_final = template.render(**contexto)
            
            output_dir = os.path.join(os.getcwd(), "relatorios_inteligencia")
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename_base = f"Jornal_{topico.replace(' ', '_')}_{timestamp}"
            path_html = os.path.join(output_dir, f"{filename_base}.html")
            path_pdf = os.path.join(output_dir, f"{filename_base}.pdf")
            
            # Caminho absoluto é crucial para o Playwright
            abs_path_html = os.path.abspath(path_html)
            
            with open(path_html, "w", encoding="utf-8") as f:
                f.write(html_final)

            # 6. GERAÇÃO DE PDF COM PLAYWRIGHT (MODERNO E SEGURO)
            msg_final = f"HTML gerado: {path_html}"

            if sync_playwright:
                logger.info("🚀 Iniciando motor Chromium (Playwright)...")
                try:
                    with sync_playwright() as p:
                        # Lança o navegador
                        browser = p.chromium.launch(headless=True)
                        page = browser.new_page()
                        
                        # --- CARREGAMENTO OTIMIZADO (TIMEOUT 100s) ---
                        # wait_until="domcontentloaded": Não trava em imagens lentas
                        page.goto(f"file:///{abs_path_html}", wait_until="domcontentloaded", timeout=100000)
                        
                        # --- ESPERA INTELIGENTE PELO LAYOUT (TIMEOUT 200s) ---
                        # Espera até que o JS adicione a classe 'ready'
                        try:
                            page.wait_for_selector("body.ready", timeout=200000) 
                        except:
                            logger.warning("⚠️ Timeout esperando paginação JS. Imprimindo assim mesmo.")

                        # Gera o PDF
                        page.pdf(
                            path=path_pdf,
                            format="A4",
                            print_background=True,
                            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"}
                        )
                        browser.close()
                        
                    msg_final = f"Relatório PDF de Alta Definição gerado: {path_pdf}"
                    
                    # 7. ENVIO PARA O WHATSAPP (INTEGRAÇÃO J.A.R.V.I.S.)
                    try:
                        # Importação lazy para evitar erro se o arquivo não existir
                        from .whatsapp_sender import WhatsAppSender 
                        
                        zap = WhatsAppSender()
                        grupo_destino = "noticias jarvis" 
                        
                        logger.info(f"📤 Enviando PDF para: {grupo_destino}...")
                        zap.enviar_arquivo(grupo_destino, path_pdf)
                        
                        msg_final += f" | 📤 Enviado para '{grupo_destino}'"
                    
                    except ImportError:
                        logger.warning("⚠️ whatsapp_sender.py não encontrado. Pulei o envio.")
                    except Exception as e_zap:
                        logger.error(f"Erro no envio WhatsApp: {e_zap}")
                        msg_final += " (Falha no envio Zap)"

                except Exception as e_playwright:
                    logger.error(f"Erro Playwright: {e_playwright}")
                    msg_final = f"Erro no PDF (HTML salvo): {path_html}"
            else:
                msg_final = f"Playwright não instalado. Apenas HTML gerado: {path_html}"
            
            return f"Senhor, {msg_final}"

        except Exception as e:
            logger.error(f"Erro renderização: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return "Erro na gráfica, senhor."

    def _fluxo_apenas_voz(self, topico, intent, dados):
        if not self.agent_llm or not prompts: return "Modo Offline."
        prompt_voz = prompts.get_synthesis_prompt(topico, intent, json.dumps(dados, ensure_ascii=False), mode="voz")
        resp = self.agent_llm.run(prompt_voz)
        return resp.content if hasattr(resp, 'content') else str(resp)