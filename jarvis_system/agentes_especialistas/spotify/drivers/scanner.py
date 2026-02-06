import socket
import platform
import os

def obter_nome_computador():
    """
    Retorna o nome da máquina local.
    O Spotify Desktop geralmente usa este nome como identificador no Connect.
    """
    try:
        # Tentativa 1: Nome de Host padrão (mais confiável)
        nome = socket.gethostname()
        
        # Tentativa 2: Variável de Ambiente do Windows (caso a 1 falhe)
        if not nome:
            nome = os.environ.get('COMPUTERNAME')
            
        # Tentativa 3: Plataforma
        if not nome:
            nome = platform.node()
            
        return nome
    except Exception as e:
        print(f"Erro ao detectar nome: {e}")
        return "JARVAS" # Fallback se tudo der errado

if __name__ == "__main__":
    pc_name = obter_nome_computador()
    print(f"\n🖥️  NOME DESTE COMPUTADOR: [{pc_name}]")
    print("ℹ️  O Spotify provavelmente usa este nome na lista de dispositivos.")