import os
import sys

# Importa o Mega Agente
from jarvis_system.hipocampo.curador_musical import CuradorMusical

# Importa o Scraper (se existir)
try:
    from jarvis_system.hipocampo.absorver_spotify_v3 import menu as menu_scraper
except ImportError:
    menu_scraper = None

def limpar_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    agente = CuradorMusical()
    
    while True:
        limpar_terminal()
        print("🎵 J.A.R.V.I.S. - CENTRAL DE CONTROLE MUSICAL")
        print("="*50)
        print("1. 📥 Absorver Spotify (Novo Scraper)")
        print("2. 🧹 Faxina Geral (Gêneros e Lixo)")
        print("3. ⏳ Buscar Anos (iTunes API)")
        print("4. 🚑 Aplicar Patch Manual (Correção de Virais/Trap)")
        print("5. 📊 Gerar Relatório Tabela (.txt)")
        print("6. 🎧 Modo DJ")
        print("0. ❌ Sair")
        print("="*50)
        
        opt = input("Escolha uma missão: ")
        
        if opt == "1":
            if menu_scraper: menu_scraper()
            else: print("Scraper não encontrado.")
            input("\n[Enter]...")
        elif opt == "2":
            agente.remover_lixo()
            agente.refinar_generos()
            input("\n[Enter]...")
        elif opt == "3":
            agente.buscar_anos_faltantes()
            input("\n[Enter]...")
        elif opt == "4":
            agente.aplicar_patch_manual()
            input("\n[Enter]...")
        elif opt == "5":
            agente.gerar_relatorio()
            input("\n[Enter]...")
        elif opt == "6":
            cmd = input("\nO que devo tocar? ")
            agente.tocar_dj(cmd)
            input("\n[Enter]...")
        elif opt == "0":
            break

if __name__ == "__main__":
    main()