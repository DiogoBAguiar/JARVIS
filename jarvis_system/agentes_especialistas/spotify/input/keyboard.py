import time
import logging
import pyautogui

logger = logging.getLogger("INPUT_KEYBOARD")

class KeyboardMacroHandler:
    """
    Responsável por automação de alto nível (Teclado/Mouse Global).
    Usa PyAutoGUI para simular usuário real.
    """

    def __init__(self):
        # Mapa de Comandos -> Atalhos
        self.mapa_atalhos = {
            # Execução Básica
            "play_pause": "space",
            "next": ["ctrl", "right"],
            "prev": ["ctrl", "left"],
            "seek_fwd": ["shift", "right"],
            "seek_back": ["shift", "left"],
            
            # Volume
            "vol_up": ["ctrl", "up"],
            "vol_down": ["ctrl", "down"],
            "mute": ["ctrl", "shift", "down"],
            
            # Navegação e Utilidades
            "shuffle": ["ctrl", "s"],
            "repeat": ["ctrl", "r"],
            "like": ["alt", "shift", "b"], # Atalho padrão pode variar, ajustado para Alt+Shift+B (Heart) ou similar
            "nav_search": ["ctrl", "l"]
        }

    def executar_comando_midia(self, comando: str):
        """Executa um comando mapeado no dicionário."""
        if comando in self.mapa_atalhos:
            atalho = self.mapa_atalhos[comando]
            try:
                if isinstance(atalho, list):
                    pyautogui.hotkey(*atalho)
                else:
                    pyautogui.press(atalho)
                logger.info(f"⌨️ Input enviado: {comando} -> {atalho}")
            except Exception as e:
                logger.error(f"Erro ao enviar input: {e}")
        else:
            logger.warning(f"Comando desconhecido: {comando}")

    def digitar_busca(self, query: str):
        """Fluxo completo de busca: Atalho -> Digita -> Enter."""
        # 1. Foca barra de busca
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(0.4) 
        
        # 2. Digita
        pyautogui.write(query, interval=0.01) 
        time.sleep(0.5) 
        
        # 3. Confirma
        pyautogui.press('enter')

    def rolar_pagina(self, direcao="down", qtd=3):
        """Simula PageUp / PageDown."""
        key = 'pgdn' if direcao == "down" else 'pgup'
        for _ in range(qtd):
            pyautogui.press(key)
            time.sleep(0.1)