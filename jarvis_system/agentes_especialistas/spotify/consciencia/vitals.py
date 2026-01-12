import psutil
import requests
import logging

logger = logging.getLogger("CONSCIENCIA_VITAIS")

class VitalsMonitor:
    """
    Monitora a saúde física do sistema (Hardware e Rede).
    Responde à pergunta: 'Tenho recursos para agir?'
    """

    def check_system_health(self):
        """Retorna um check-up rápido de CPU e Memória."""
        return {
            "cpu_usage": psutil.cpu_percent(interval=None),
            "memory_usage": psutil.virtual_memory().percent,
            "battery": self._check_battery()
        }

    def check_connectivity(self):
        """
        Ping rápido para verificar acesso ao mundo exterior.
        Critical para serviços de streaming como Spotify.
        """
        try:
            # Tenta conectar ao Google DNS (rápido e confiável)
            requests.get("https://8.8.8.8", timeout=1.5)
            return True
        except requests.RequestException:
            logger.warning("⚠️ Perda de conexão com a internet detectada.")
            return False

    def _check_battery(self):
        """Retorna porcentagem da bateria ou None se for Desktop."""
        if not hasattr(psutil, "sensors_battery"): return None
        
        battery = psutil.sensors_battery()
        return battery.percent if battery else None