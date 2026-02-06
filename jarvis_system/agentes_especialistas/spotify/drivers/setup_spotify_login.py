import os
from playwright.sync_api import sync_playwright

def configurar_login_edge():
    # Caminho onde salvaremos a sessão (Cookies)
    session_dir = os.path.join(os.getcwd(), "jarvis_system", "agentes_especialistas", "spotify", "drivers", "spotify_web_session")
    os.makedirs(session_dir, exist_ok=True)

    print("🚀 Abrindo MICROSOFT EDGE para Login...")
    
    with sync_playwright() as p:
        # channel="msedge" força o uso do Edge instalado no Windows
        # Isso ativa o DRM (Widevine) automaticamente
        browser = p.chromium.launch_persistent_context(
            user_data_dir=session_dir,
            channel="msedge",  # <--- O SEGREDO ESTÁ AQUI
            headless=False,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
            no_viewport=True
        )
        
        page = browser.pages[0]
        page.goto("https://open.spotify.com/")
        
        print("✅ Edge aberto! O erro de 'Conteúdo Protegido' não deve aparecer.")
        print("👉 Faça login, coloque uma música para tocar (garanta que sai som) e depois dê ENTER aqui.")
        
        input("Pressione ENTER após confirmar que o áudio está funcionando...")
        
        browser.close()
        print("💾 Sessão do Edge salva com sucesso!")

if __name__ == "__main__":
    configurar_login_edge()