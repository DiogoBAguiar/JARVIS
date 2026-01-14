import os
import sys

# Garante que o Python encontre a raiz do projeto (3 níveis acima)
# Ajusta o path para: jarvis/
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
sys.path.append(project_root)

# Importa a Fachada Unificada de Memória Musical
from jarvis_system.hipocampo.pensamento_musical import CuradorMusical

# Importa o Cérebro Especialista (Agente)
from jarvis_system.agentes_especialistas.spotify.agent import AgenteSpotify

def limpar_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    # Instancia o Gerente Geral de Música (Fachada)
    jarvis_music = CuradorMusical()
    
    # Instancia o Agente Inteligente (Controlador)
    agente_inteligente = AgenteSpotify()
    
    while True:
        limpar_terminal()
        print("🎵 J.A.R.V.I.S. - CONSOLE ADMINISTRATIVO (V3 MODULAR)")
        print("="*60)
        print("1. 📥 Absorver Likes (Scraper + IA)")
        print("2. 📥 Absorver Playlist Específica")
        print("3. 🧹 Faxina Geral & Nomes (Frei Gilson, etc)") # <-- Atualizado
        print("4. ⏳ Buscar Anos (iTunes API)")
        print("5. 🚑 Aplicar Patch Manual (Anos/Gêneros)")
        print("6. 📊 Gerar Relatório Tabela")
        print("7. 🎧 Testar Agente (Modo DJ / Comandos de Voz)")
        print("0. ❌ Sair")
        print("="*60)
        
        opt = input("Escolha uma missão: ")
        
        if opt == "1":
            jarvis_music.absorver_novas_musicas(mode="likes")
            input("\n[Enter]...")
        elif opt == "2":
            nome = input("Nome da playlist (ex: louvor): ")
            jarvis_music.absorver_novas_musicas(mode="playlist", playlist=nome)
            input("\n[Enter]...")
        elif opt == "3":
            print("\n--- INICIANDO FAXINA COMPLETA ---")
            jarvis_music.remover_lixo()
            
            # --- AQUI ESTAVA FALTANDO ESSA LINHA: ---
            # Se der erro aqui, verifique se você atualizou o core.py para ter esse método!
            try:
                jarvis_music.corrigir_nomes() 
            except AttributeError:
                print("⚠️ Erro: Método 'corrigir_nomes' não encontrado no Curador. Atualize o core.py!")
            
            jarvis_music.refinar_generos()
            print("--- FAXINA CONCLUÍDA ---")
            input("\n[Enter]...")
        elif opt == "4":
            jarvis_music.buscar_anos_faltantes()
            input("\n[Enter]...")
        elif opt == "5":
            jarvis_music.aplicar_patch_manual()
            input("\n[Enter]...")
        elif opt == "6":
            jarvis_music.gerar_relatorio()
            input("\n[Enter]...")
        elif opt == "7":
            print("\n💡 Dica: Digite 'tocar [musica]' ou comandos normais.")
            cmd = input("Comando para o Agente: ")
            
            if "tocar" not in cmd.lower() and "play" not in cmd.lower() and "clique" not in cmd.lower():
                 comando_real = f"tocar {cmd}"
            else:
                 comando_real = cmd

            print(f"\n🤖 [Agente] Processando: '{comando_real}'...")
            resposta = agente_inteligente.executar(comando_real)
            print(f"💬 Resposta: {resposta}")
            input("\n[Enter]...")
        elif opt == "0":
            break

if __name__ == "__main__":
    main()