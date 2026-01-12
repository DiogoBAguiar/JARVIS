import sys
import os
import logging
import time
import traceback
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configura log para vermos as estratégias sendo ativadas
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TESTE_INTEGRADO")

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    print("\n🚀 INICIALIZANDO JARVIS SPOTIFY (MODULAR)...")
    print("-" * 60)

    agente = None

    # --- BLOCO DE INICIALIZAÇÃO ---
    try:
        from jarvis_system.agentes_especialistas.spotify.agent import AgenteSpotify
        agente = AgenteSpotify()
    except ImportError as e:
        print(f"\n❌ ERRO FATAL DE IMPORTAÇÃO: Não foi possível carregar o Agente.")
        print(f"Detalhe: {e}")
        return
    except Exception as e:
        print(f"\n❌ ERRO FATAL NA INICIALIZAÇÃO: {e}")
        traceback.print_exc()
        return

    # ---------------------------------------------------------
    # 🩺 ETAPA 1: CHECKUP INICIAL (Com tolerância a falhas)
    # ---------------------------------------------------------
    print("\n🩺 [ETAPA 1] Checkup de Sinais Vitais")
    try:
        diagnostico = agente.consciencia.sentir_sinais_vitais()
        
        if not diagnostico['janela_spotify']:
            print("⚠️ AVISO: O sistema reportou que o Spotify não está visível.")
            print("   (Isso pode ocorrer se uma música estiver tocando e mudou o título da janela).")
            print("⚠️ Continuando o teste em MODO FORÇADO...")
            # return  <-- COMENTADO PARA NÃO PARAR O TESTE
        else:
            print("✅ Spotify Detectado e Pronto.")
    except Exception as e:
        print(f"❌ Erro ao verificar sinais vitais: {e}")
        print("⚠️ Tentando continuar mesmo assim...")

    # ---------------------------------------------------------
    # 🎵 ETAPA 2: ESTRATÉGIA DE FAIXA (TRACK)
    # ---------------------------------------------------------
    musica_teste = "Tocar Deu Onda"
    print(f"\n🎵 [ETAPA 2] Testando Estratégia de FAIXA: '{musica_teste}'")
    print("   (Isso deve clicar no filtro 'Músicas' e depois na 1ª linha)")
    
    try:
        agente.executar(musica_teste)
        
        print("⏳ Aguardando 10 segundos para você curtir a música...")
        time.sleep(10)
    except Exception as e:
        print(f"❌ FALHA na Etapa 2 (Faixa): {e}")
        traceback.print_exc()

    # ---------------------------------------------------------
    # 🎨 ETAPA 3: ESTRATÉGIA DE ARTISTA (ARTIST)
    # ---------------------------------------------------------
    artista_teste = "Frei Gilson"
    print(f"\n🎨 [ETAPA 3] Testando Estratégia de ARTISTA: '{artista_teste}'")
    print("   (Isso deve clicar no filtro 'Artistas', entrar no perfil e dar Play)")
    
    try:
        # 1. Tentar Digitar
        print(f"⌨️  Digitando '{artista_teste}' na busca...")
        try:
            agente.controller.input.buscar(artista_teste)
        except AttributeError:
            print("❌ ERRO CRÍTICO: O InputManager não tem o método '.buscar()'. Verifique se o arquivo manager.py foi salvo corretamente.")
            raise # Para a etapa 3, pois sem digitar não adianta clicar
        except Exception as e:
            print(f"❌ Erro ao digitar: {e}")
            raise

        print("⏳ Aguardando resultados carregarem...")
        time.sleep(2.5) # Tempo essencial para a interface atualizar
        
        # 2. Tentar Navegar Visualmente
        print(f"⚙️ Invocando visual_navigator.find_and_click('{artista_teste}', tipo='artista')...")
        sucesso = agente.controller.navigator.find_and_click(artista_teste, tipo="artista")
        
        if sucesso:
            print("✅ Estratégia de Artista executada com sucesso!")
        else:
            print("❌ Falha na Estratégia de Artista (Retornou False).")

    except Exception as e:
        print(f"❌ FALHA na Etapa 3 (Artista): {e}")
        # Não usamos traceback aqui para não sujar muito, a menos que seja crítico

    # ---------------------------------------------------------
    # 👁️ ETAPA 4: CONFIRMAÇÃO VISUAL (OCR)
    # ---------------------------------------------------------
    print("\n👁️ [ETAPA 4] O que está tocando agora?")
    try:
        time.sleep(3) # Espera carregar o player
        info = agente.controller.ler_musica_atual()
        if info:
            print(f"✅ Detectado: {info.get('raw', 'Desconhecida')}")
        else:
            print("⚠️ Não consegui ler o player (Retorno vazio).")
    except Exception as e:
        print(f"❌ Erro ao ler tela via OCR: {e}")

    print("\n🚀 BATERIA DE TESTES CONCLUÍDA!")
    print("-" * 60)

if __name__ == "__main__":
    main()