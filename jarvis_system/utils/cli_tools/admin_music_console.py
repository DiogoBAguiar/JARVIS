import os
import sys

# Garante que o Python encontre a raiz do projeto (3 níveis acima)
# Ajusta o path para: jarvis/
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
sys.path.append(project_root)

# Importa as Ferramentas de Memória (Hipocampo)
from jarvis_system.hipocampo.curador_musical import CuradorMusical
from jarvis_system.hipocampo.absorver_spotify_v3 import SpotifyIngestor

# Importa o Cérebro Especialista (Agente)
from jarvis_system.agentes_especialistas.spotify.agent import AgenteSpotify

def limpar_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    # Instancia as ferramentas de manutenção
    curador = CuradorMusical() # Renomeei de 'agente' para 'curador' para não confundir
    scraper = SpotifyIngestor()
    
    # Instancia o Agente Inteligente (Controlador)
    agente_inteligente = AgenteSpotify()
    
    while True:
        limpar_terminal()
        print("🎵 J.A.R.V.I.S. - CONSOLE ADMINISTRATIVO (AUDIO)")
        print("="*60)
        print("1. 📥 Absorver Likes (Scraper + IA)")
        print("2. 📥 Absorver Playlist Específica")
        print("3. 🧹 Faxina Geral & Gêneros")
        print("4. ⏳ Buscar Anos (iTunes API)")
        print("5. 🚑 Aplicar Patch Manual")
        print("6. 📊 Gerar Relatório Tabela")
        print("7. 🎧 Testar Agente (Modo DJ / Comandos de Voz)")
        print("0. ❌ Sair")
        print("="*60)
        
        opt = input("Escolha uma missão: ")
        
        if opt == "1":
            scraper.processar_extracao(mode="likes")
            input("\n[Enter]...")
        elif opt == "2":
            nome = input("Nome da playlist (ex: louvor): ")
            scraper.processar_extracao(mode="playlist", playlist_name=nome)
            input("\n[Enter]...")
        elif opt == "3":
            curador.remover_lixo()
            curador.refinar_generos()
            input("\n[Enter]...")
        elif opt == "4":
            curador.buscar_anos_faltantes()
            input("\n[Enter]...")
        elif opt == "5":
            curador.aplicar_patch_manual()
            input("\n[Enter]...")
        elif opt == "6":
            curador.gerar_relatorio()
            input("\n[Enter]...")
        elif opt == "7":
            print("\n💡 Dica: Você pode digitar nomes de músicas, ou comandos como 'pausa', 'clique em buscar', etc.")
            cmd = input("Comando para o Agente: ")
            
            # Pequeno ajuste para garantir que busca funcione se digitar só o nome
            if "tocar" not in cmd.lower() and "play" not in cmd.lower() and "clique" not in cmd.lower():
                 comando_real = f"tocar {cmd}"
            else:
                 comando_real = cmd

            print(f"\n🤖 [Agente] Processando: '{comando_real}'...")
            
            # AQUI ESTÁ A MÁGICA: O Agente assume o controle!
            resposta = agente_inteligente.executar(comando_real)
            
            print(f"💬 Resposta: {resposta}")
            input("\n[Enter]...")
        elif opt == "0":
            break

if __name__ == "__main__":
    main()