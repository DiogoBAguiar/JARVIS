J.A.R.V.I.S. (Just A Rather Very Intelligent System)
Assistente Virtual Modular com Arquitetura Biomimética e Visão Computacional.

O J.A.R.V.I.S. é um assistente pessoal avançado desenvolvido em Python, projetado para controlar o sistema operacional, gerenciar mídia e executar tarefas complexas através de comandos de voz naturais. Diferente de bots simples, ele utiliza uma arquitetura inspirada no cérebro humano (Córtex, Broca, Hipocampo) e integra LLMs (Llama 3.3) com Visão Computacional (OpenCV) para interagir com interfaces gráficas sem APIs públicas.

🧠 Arquitetura do Sistema
O projeto segue uma estrutura modular baseada em biologia cognitiva:

Cortex Frontal (Orquestrador): O "gerente" do sistema. Recebe a intenção do usuário, decide qual especialista chamar e gerencia o fluxo de execução.

Cortex Brain (LLM): O centro de raciocínio. Utiliza modelos de linguagem (Llama 3.3-70b via Groq) para entender contexto, realizar conversas complexas e estruturar dados (JSON) para os agentes.

Área de Broca (Input/Output):

Broca Ears: Subsistema de audição powered by OpenAI Whisper. Possui filtros de ruído (Noise Gate) e detecção de voz.

Broca Voice: Subsistema de fala utilizando síntese neural de alta qualidade (ex: Azure TTS / Edge TTS).

Hipocampo (Memória): Banco de dados vetorial (ChromaDB) para memória de longo prazo e contexto.

Agentes Especialistas (Motor Registry): Módulos independentes para tarefas específicas (Spotify, Clima, Sistema, Calendário).

👁️ Destaque: Integração Spotify com Visão Computacional
O agente do Spotify (agente_spotify.py) é um exemplo de Automação Híbrida:

NLU (Natural Language Understanding): Interpreta o comando (ex: "Tocar 30 pra 1") e classifica entre Track, Artist ou Playlist.

Correção Fonética: Corrige erros comuns do reconhecimento de voz (ex: "3-1" -> "30PRAUM").

Visão Computacional (OpenCV):

Ao abrir páginas de Artistas/Playlists, o Jarvis escaneia a tela em busca do botão "Play" verde.

Possui modo Colorido e Grayscale (daltônico) para lidar com fundos dinâmicos do Spotify.

Fallback Cego: Se a visão falhar, utiliza automação de teclado (Hotkeys) como backup.

🛠️ Tecnologias Utilizadas
Linguagem: Python 3.12+

IA & NLP: groq (Llama 3.3), openai-whisper (Speech-to-Text).

Automação & Visão: pyautogui, opencv-python, pygetwindow.

Áudio: speechrecognition, pygame, pyaudio.

Estrutura de Dados: json, re.

J.A.R.V.I.S/
│
├── main.py                     # Ponto de entrada (Inicia o Kernel)
├── requirements.txt            # Dependências (OpenCV, PyAutoGUI, etc.)
├── .env                        # Chaves de API (Groq, OpenAI, etc.)
│
├── img/                        # Memória Visual (Assets para OpenCV)
│   └── play_spotify.png        # Referência visual do botão Play verde
│
└── jarvis_system/              # Núcleo do Sistema
    │
    ├── protocol.py               # Loop principal e gestão de estado
    │
    ├── cortex_frontal/         # Inteligência e Decisão
    │   ├── brain_llm.py        # Integração com LLM (Llama 3.3)
    │   └── orchestrator.py     # Lógica de decisão de fluxo
    │
    ├── subsistemas/ (ou raiz do system)
    │   ├── broca_ears.py       # Audição (Whisper + Noise Gate)
    │   ├── broca_voice.py      # Fala (TTS Neural)
    │   └── hipocampo_reflexos.py # Memória rápida e atalhos
    │
    ├── motor/
    │   ├── motor_registry.py   # Carregador de Agentes
    │   └── motor_launcher.py   # Indexador de Programas do Windows
    │
    └── agentes_especialistas/  # Habilidades Específicas
        ├── base_agente.py      # Classe base (Herança)
        ├── agente_spotify.py   # Controlador Spotify (Híbrido: Visão + API)
        ├── agente_clima.py     # Previsão do tempo
        ├── agente_sistema.py   # Controle de volume e janelas
        ├── agente_calendario.py# Agenda e compromissos
        └── agente_media.py     # Controle genérico de mídia
🚀 Instalação e Configuração
1. Pré-requisitos
Python 3.10 ou superior.

Conta na Groq (para API Key do LLM).

Spotify Desktop instalado.

2. Instalação
Clone o repositório e instale as dependências:

Bash

git clone https://github.com/seu-usuario/jarvis-v2.git
cd jarvis-v2
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
3. Configuração de Visão
Para o agente do Spotify funcionar corretamente:

Abra o Spotify Desktop.

Tire um print (Win + Shift + S) apenas do botão Play verde (círculo com triângulo).

Salve a imagem como img/play_spotify.png na raiz do projeto.

4. Execução
Bash

python main.py
🎮 Comandos de Exemplo
Música: "Jarvis, tocar 30 pra 1" (Correção automática para 30PRAUM).

Música Específica: "Tocar a música Faroeste Caboclo".

Sistema: "Abrir navegador", "Volume 50%".

Conversa: "Jarvis, quem foi Nikola Tesla?"

⚠️ Solução de Problemas Comuns
Jarvis não clica no botão: Verifique se a imagem img/play_spotify.png existe e foi recortada sem margens excessivas. O mouse não deve estar em cima do botão na hora do print.

Ouvido captando ruído: Ajuste o energy_threshold no arquivo broca_ears.py para ~3000.