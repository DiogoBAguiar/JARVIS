import cv2
import threading
import time
import atexit
import os
from abc import ABC, abstractmethod
from typing import Optional
from enum import Enum
from onvif import ONVIFCamera

# --- Enumerações e Abstrações de Estado ---

class EstadoDirecional(Enum):
    """Representa a máquina de estados do motor PTZ."""
    PARADO = 0
    MOVENDO_CIMA = 1
    MOVENDO_BAIXO = 2
    MOVENDO_ESQUERDA = 3
    MOVENDO_DIREITA = 4

# --- Abstrações de Visão e Mecânica ---

class InterfaceDeVisao(ABC):
    """Contrato rigoroso para captura de vídeo."""
    @abstractmethod
    def estabelecer_conexao(self) -> bool: pass
    
    @abstractmethod
    def extrair_quadro(self): pass
    
    @abstractmethod
    def liberar_recursos_alocados(self): pass

class InterfaceDeMovimentacaoPTZ(ABC):
    """Contrato para controle mecânico de eixos (Pan/Tilt/Zoom) e periféricos."""
    @abstractmethod
    def autenticar_motor(self) -> bool: pass

    @abstractmethod
    def mover_continuamente(self, eixo_x: float, eixo_y: float): pass

    @abstractmethod
    def interromper_movimento(self): pass

    @abstractmethod
    def alternar_luzes(self, ligar: bool): pass

# --- Implementações de Hardware (Comunicação de Vídeo Otimizada) ---

class MotorDeCapturaAssincrona(InterfaceDeVisao):
    """
    Implementação avançada que utiliza multithreading para esgotar o buffer RTSP.
    Garante latência zero (Real-Time) ao manter apenas o quadro mais recente na memória.
    """
    def __init__(self, identificador_de_fluxo: str):
        self._identificador_de_fluxo = identificador_de_fluxo
        self._objeto_captura: Optional[cv2.VideoCapture] = None
        
        # Variáveis de estado compartilhadas entre as threads (Composição de Estado)
        self._ultimo_quadro_processado = None
        self._status_de_leitura = False
        self._thread_em_execucao = False
        self._trava_de_memoria = threading.Lock()

    def estabelecer_conexao(self) -> bool:
        # Configuração agressiva para forçar o protocolo a usar TCP e zerar o buffer
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
        
        self._objeto_captura = cv2.VideoCapture(self._identificador_de_fluxo, cv2.CAP_FFMPEG)
        self._objeto_captura.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not self._objeto_captura.isOpened():
            return False

        # Inicia a thread que rodará em paralelo ao sistema principal
        self._status_de_leitura, self._ultimo_quadro_processado = self._objeto_captura.read()
        self._thread_em_execucao = True
        
        thread_de_leitura = threading.Thread(target=self._atualizar_quadro_continuamente, daemon=True)
        thread_de_leitura.start()
        
        # Garante que o recurso seja liberado se o script for morto subitamente
        atexit.register(self.liberar_recursos_alocados)
        
        return True

    def _atualizar_quadro_continuamente(self):
        """Thread bloqueante que consome o fluxo de rede na velocidade máxima."""
        while self._thread_em_execucao:
            if self._objeto_captura is not None and self._objeto_captura.isOpened():
                sucesso, quadro_lido = self._objeto_captura.read()
                
                # Utiliza Mutex (Lock) para evitar que a matriz seja corrompida durante a leitura
                with self._trava_de_memoria:
                    self._status_de_leitura = sucesso
                    if sucesso:
                        self._ultimo_quadro_processado = quadro_lido

    def extrair_quadro(self):
        """Método de acesso rápido para o orquestrador (latência zero)."""
        with self._trava_de_memoria:
            if self._status_de_leitura and self._ultimo_quadro_processado is not None:
                # Retorna uma cópia da matriz para garantir a integridade dos dados no pipeline
                return self._ultimo_quadro_processado.copy()
        return None

    def liberar_recursos_alocados(self):
        self._thread_em_execucao = False
        if self._objeto_captura is not None:
            self._objeto_captura.release()

class CameraIPMonitoramento(MotorDeCapturaAssincrona):
    """Especialização do motor assíncrono para montagem dinâmica de credenciais RTSP."""
    def __init__(self, endereco_ip: str, porta_rtsp: int, usuario: str, senha: str):
        url_de_transmissao = f"rtsp://{usuario}:{senha}@{endereco_ip}:{porta_rtsp}/stream"
        super().__init__(url_de_transmissao)

# --- Implementações de Hardware (Comunicação Mecânica e Periféricos) ---

class MotorMecanicoONVIF(InterfaceDeMovimentacaoPTZ):
    """Especialização responsável por enviar comandos SOAP para motores PTZ e relés."""
    def __init__(self, endereco_ip: str, porta_onvif: int, usuario: str, senha: str):
        self._endereco_ip = endereco_ip
        self._porta_onvif = porta_onvif
        self._usuario = usuario
        self._senha = senha
        
        self._camera_onvif: Optional[ONVIFCamera] = None
        self._servico_ptz = None
        self._token_do_perfil_de_midia = None
        self._estrutura_velocidade_base = None

    def autenticar_motor(self) -> bool:
        try:
            print(f"Negociando chaves de controle mecânico na porta {self._porta_onvif}...")
            self._camera_onvif = ONVIFCamera(self._endereco_ip, self._porta_onvif, self._usuario, self._senha)
            
            servico_de_midia = self._camera_onvif.create_media_service()
            perfis_de_midia = servico_de_midia.GetProfiles()
            self._token_do_perfil_de_midia = perfis_de_midia[0].token
            
            self._servico_ptz = self._camera_onvif.create_ptz_service()
            
            status_inicial = self._servico_ptz.GetStatus({'ProfileToken': self._token_do_perfil_de_midia})
            self._estrutura_velocidade_base = status_inicial.Position
            
            return True
        except Exception as excecao:
            print(f"[ERRO PTZ] Falha na comunicação de controle: {excecao}")
            return False

    def _executar_requisicao_em_paralelo(self, comando: callable, argumento_requisicao):
        """Isola a requisição de rede em uma thread segura."""
        def tarefa_isolada():
            try:
                comando(argumento_requisicao)
            except Exception as erro_rede:
                print(f"\n[ALERTA MECÂNICO/PERIFÉRICO] A câmera rejeitou o comando: {erro_rede}")

        thread_de_comando = threading.Thread(target=tarefa_isolada)
        thread_de_comando.start()

    def mover_continuamente(self, eixo_x: float, eixo_y: float):
        if not self._servico_ptz or not self._estrutura_velocidade_base:
            return

        requisicao_de_movimento = self._servico_ptz.create_type('ContinuousMove')
        requisicao_de_movimento.ProfileToken = self._token_do_perfil_de_midia
        
        requisicao_de_movimento.Velocity = self._estrutura_velocidade_base
        requisicao_de_movimento.Velocity.PanTilt.x = eixo_x
        requisicao_de_movimento.Velocity.PanTilt.y = eixo_y

        self._executar_requisicao_em_paralelo(self._servico_ptz.ContinuousMove, requisicao_de_movimento)

    def interromper_movimento(self):
        if not self._servico_ptz:
            return

        requisicao_de_parada = self._servico_ptz.create_type('Stop')
        requisicao_de_parada.ProfileToken = self._token_do_perfil_de_midia
        requisicao_de_parada.PanTilt = True
        requisicao_de_parada.Zoom = False

        self._executar_requisicao_em_paralelo(self._servico_ptz.Stop, requisicao_de_parada)

    def alternar_luzes(self, ligar: bool):
        """Tenta enviar o comando ONVIF universal de ativação de relé/luzes brancas."""
        if not self._servico_ptz:
            return

        requisicao_auxiliar = self._servico_ptz.create_type('SendAuxiliaryCommand')
        requisicao_auxiliar.ProfileToken = self._token_do_perfil_de_midia
        
        # 'LightOn' e 'LightOff' são as strings padrão ONVIF para iluminação
        comando_texto = 'LightOn' if ligar else 'LightOff'
        requisicao_auxiliar.AuxiliaryData = comando_texto

        print(f"Tentando acionar periférico via ONVIF: {comando_texto}")
        self._executar_requisicao_em_paralelo(self._servico_ptz.SendAuxiliaryCommand, requisicao_auxiliar)

# --- Componentes de Apresentação e Controle Lógico ---

class RenderizadorDeInterface:
    """Gerencia a renderização de vídeo e intercepta os comandos (Motor e Periféricos)."""
    def __init__(self, titulo_da_janela: str, motor_ptz: InterfaceDeMovimentacaoPTZ):
        self._titulo_da_janela = titulo_da_janela
        self._motor_ptz = motor_ptz
        
        # Controle de Estado e Tempo (Debouncing)
        self._estado_atual = EstadoDirecional.PARADO
        self._momento_ultima_interacao = time.time()
        self._limiar_de_inatividade = 0.15 
        
        # Estado do relé das lanternas
        self._estado_das_luzes = False
        self._momento_ultimo_interruptor = time.time()

    def _processar_mudanca_de_estado(self, novo_estado: EstadoDirecional, velocidade_x: float, velocidade_y: float):
        """Garante que o comando de rede só seja disparado se houver real mudança de estado."""
        self._momento_ultima_interacao = time.time()
        
        if self._estado_atual != novo_estado:
            self._motor_ptz.mover_continuamente(velocidade_x, velocidade_y)
            self._estado_atual = novo_estado

    def renderizar_matriz_de_pixels(self, matriz_imagem) -> bool:
        if matriz_imagem is not None:
            matriz_redimensionada = cv2.resize(matriz_imagem, (1024, 768))
            
            # Interface de instruções atualizada
            cv2.putText(matriz_redimensionada, "W/A/S/D: Mover Camera", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(matriz_redimensionada, "L: Ligar/Desligar Lanternas", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(matriz_redimensionada, "Q: Sair", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            cv2.imshow(self._titulo_da_janela, matriz_redimensionada)
            
            tecla_pressionada = cv2.waitKey(1) & 0xFF
            
            if tecla_pressionada == ord('w'):
                self._processar_mudanca_de_estado(EstadoDirecional.MOVENDO_CIMA, 0.0, 0.5)
            elif tecla_pressionada == ord('s'):
                self._processar_mudanca_de_estado(EstadoDirecional.MOVENDO_BAIXO, 0.0, -0.5)
            elif tecla_pressionada == ord('a'):
                self._processar_mudanca_de_estado(EstadoDirecional.MOVENDO_ESQUERDA, -0.5, 0.0)
            elif tecla_pressionada == ord('d'):
                self._processar_mudanca_de_estado(EstadoDirecional.MOVENDO_DIREITA, 0.5, 0.0)
            elif tecla_pressionada == ord('l'):
                # Debouncing de meio segundo para evitar flood de rede no relé de luz
                if time.time() - self._momento_ultimo_interruptor > 0.5:
                    self._estado_das_luzes = not self._estado_das_luzes
                    self._motor_ptz.alternar_luzes(self._estado_das_luzes)
                    self._momento_ultimo_interruptor = time.time()
            elif tecla_pressionada == ord('q') or tecla_pressionada == 27:
                return False
            else:
                # Lógica de Key Up
                tempo_decorrido = time.time() - self._momento_ultima_interacao
                if self._estado_atual != EstadoDirecional.PARADO and tempo_decorrido > self._limiar_de_inatividade:
                    self._motor_ptz.interromper_movimento()
                    self._estado_atual = EstadoDirecional.PARADO

        return True

    def desconstruir_interface(self):
        cv2.destroyAllWindows()

# --- Orquestração do Subsistema ---

class SubsistemaDeControleTotal:
    """Núcleo integrador (Composição) que orquestra vídeo, interface e motor."""
    def __init__(self, fonte_de_video: InterfaceDeVisao, mecanismo_renderizacao: RenderizadorDeInterface, motor_ptz: InterfaceDeMovimentacaoPTZ):
        self._fonte_de_video = fonte_de_video
        self._mecanismo_renderizacao = mecanismo_renderizacao
        self._motor_ptz = motor_ptz

    def iniciar_operacao(self):
        print("Iniciando J.A.R.V.I.S. Visual and Mechanical Systems...")
        
        if not self._motor_ptz.autenticar_motor():
            print("[AVISO] Operando sem suporte mecânico. Apenas vídeo estará disponível.")
        else:
            print("[OK] Sistema motor engajado. Calibração PTZ pronta.")

        if not self._fonte_de_video.estabelecer_conexao():
            print("[ERRO] Falha no link óptico.")
            return

        print("[OK] Link de vídeo ativo. Janela de operação aberta.")
        
        try:
            while True:
                matriz_do_frame = self._fonte_de_video.extrair_quadro()
                if matriz_do_frame is not None:
                    if not self._mecanismo_renderizacao.renderizar_matriz_de_pixels(matriz_do_frame):
                        break
        finally:
            print("Desligando sistemas...")
            self._motor_ptz.interromper_movimento()
            self._fonte_de_video.liberar_recursos_alocados()
            self._mecanismo_renderizacao.desconstruir_interface()

# --- Ponto de Entrada ---

def inicializar_modulo_hibrido():
    ip_da_camera = "192.168.0.120"
    porta_rtsp = 554
    porta_onvif = 8899
    usuario_autenticacao = "admin"
    senha_autenticacao = "" 

    camera_principal = CameraIPMonitoramento(ip_da_camera, porta_rtsp, usuario_autenticacao, senha_autenticacao)
    motor_de_eixos = MotorMecanicoONVIF(ip_da_camera, porta_onvif, usuario_autenticacao, senha_autenticacao)
    
    tela_de_saida = RenderizadorDeInterface("J.A.R.V.I.S. - Painel de Controle Operacional", motor_de_eixos)
    
    jarvis_vision = SubsistemaDeControleTotal(camera_principal, tela_de_saida, motor_de_eixos)
    jarvis_vision.iniciar_operacao()

if __name__ == "__main__":
    inicializar_modulo_hibrido()