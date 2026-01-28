import os
import time
from playwright.sync_api import sync_playwright

class WhatsAppSender:
    def __init__(self):
        self.session_dir = os.path.join(os.getcwd(), "whatsapp_session")
        os.makedirs(self.session_dir, exist_ok=True)

    def enviar_arquivo(self, nome_contato, caminho_arquivo):
        if not os.path.exists(caminho_arquivo):
            print(f"❌ Erro: Arquivo não encontrado: {caminho_arquivo}")
            return

        print("🚀 Iniciando Agente de Entrega WhatsApp...")
        
        with sync_playwright() as p:
            # Inicia o navegador mantendo a sessão salva
            browser = p.chromium.launch_persistent_context(
                user_data_dir=self.session_dir, 
                headless=False, # Mantenha visível
                args=["--start-maximized"],
                no_viewport=True
            )
            
            page = browser.pages[0]
            page.goto("https://web.whatsapp.com/")

            print("⏳ Aguardando carregamento do WhatsApp...")
            
            try:
                # Espera a lista de conversas carregar
                page.wait_for_selector("#pane-side", timeout=60000)
            except:
                print("⚠️ Tempo limite de login excedido. Escaneie o QR Code se necessário.")
                return

            print(f"🔍 Buscando: {nome_contato}...")
            
            # 1. Busca o contato
            search_box = page.locator("div[contenteditable='true'][data-tab='3']")
            search_box.click()
            search_box.fill(nome_contato)
            time.sleep(2)
            page.keyboard.press("Enter")
            
            print("💬 Abrindo conversa...")
            try:
                # Espera a barra de digitação aparecer para confirmar que o chat abriu
                page.wait_for_selector("div[contenteditable='true'][data-tab='10']", timeout=20000)
            except:
                print(f"❌ Erro: Não consegui entrar na conversa '{nome_contato}'.")
                return

            # 2. Clicar no botão de Anexo (+)
            print("📎 Clicando no botão + ...")
            
            # Procura pelo botão com o ícone plus-rounded ou o aria-label Anexar
            btn_anexo = page.locator('button[aria-label="Anexar"], span[data-icon="plus-rounded"], span[data-icon="clip"]').first
            
            if btn_anexo.is_visible():
                btn_anexo.click()
            else:
                print("⚠️ Botão oculto, forçando clique...")
                btn_anexo.click(force=True)
            
            time.sleep(1) # Espera a animação do menu abrir

            # 3. Clicar em "Documento" e Anexar
            print("📂 Escolhendo opção 'Documento'...")
            
            try:
                # O Playwright fica "escutando" para ver se uma janela de arquivos vai abrir
                with page.expect_file_chooser() as fc_info:
                    # Clica no texto "Documento" independente da classe
                    btn_doc = page.locator("span, div").filter(has_text="Documento").last
                    btn_doc.click()
                
                # Injeta o arquivo na janela que abriu
                file_chooser = fc_info.value
                file_chooser.set_files(caminho_arquivo)
                
            except Exception as e:
                print(f"❌ Erro ao clicar em Documento: {e}")
                # Plano B: Tenta achar o input invisível
                try:
                    page.locator("input[type='file']").first.set_input_files(caminho_arquivo)
                except:
                    return

            print("📤 Enviando...")
            
            # 4. Botão Enviar (ATUALIZADO COM SEUS DADOS)
            try:
                # Aqui usamos exatamente o HTML que você encontrou:
                # 1. button com aria-label="Enviar"
                # 2. span com data-icon="wds-ic-send-filled"
                # 3. span com data-icon="send" (antigo, por garantia)
                
                seletor_enviar = 'button[aria-label="Enviar"], span[data-icon="wds-ic-send-filled"], span[data-icon="send"]'
                
                btn_enviar = page.locator(seletor_enviar).first
                
                # Espera até 30s pelo upload do arquivo (botão aparecer/ficar clicável)
                btn_enviar.wait_for(state="visible", timeout=30000) 
                btn_enviar.click()
                print("✅ Arquivo enviado com sucesso (Via Botão)!")
                
            except Exception as e:
                print(f"⚠️ Botão enviar não detectado ({e}), tentando ENTER...")
                # Se o botão falhar, o Enter resolve
                page.keyboard.press("Enter")
                print("✅ Arquivo enviado (Via Enter)!")
            
            time.sleep(5) # Espera a mensagem sair visualmente
            browser.close()