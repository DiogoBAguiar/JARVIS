# J.A.R.V.I.S. (Just A Rather Very Intelligent System)
### Arquitetura Cognitiva Modular Híbrida com Visão Computacional

O **J.A.R.V.I.S.** é um assistente pessoal avançado, projetado com uma arquitetura biomimética inspirada no cérebro humano. Diferente de bots lineares, ele opera sobre um **Barramento de Eventos (Event-Driven)**, permitindo processamento assíncrono, resiliência a falhas e raciocínio híbrido (Nuvem + Local).

O sistema integra LLMs modernos (Llama 3 via Groq e Ollama Local), Visão Computacional e controlo de sistema operacional, orquestrados por um Kernel em Python.

---

## 🧠 Arquitetura do Sistema (Biomimética v2)

O projeto foi refatorado para eliminar acoplamento direto, utilizando um sistema de **Pub/Sub** global.

### 1. Córtex Frontal (Orquestração & Decisão)
* **Orchestrator (`orchestrator.py`):** O "Gerente". Avalia intenções, gere a Janela de Atenção e decide se o input requer uma ferramenta, memória ou conversa livre.
* **Hybrid Brain (`brain_llm.py`):** Motor de inferência com estratégia de **Fallback Inteligente**:
    1.  Tenta **Nuvem** (Groq/Llama-3.3-70b) para velocidade e precisão.
    2.  Em caso de falha/offline, assume **Local** (Ollama/Qwen/Llama3) automaticamente.
* **Event Bus (`event_bus.py`):** A "medula espinhal". Desacopla os sensores (Ouvido) dos atuadores (Fala/Apps), permitindo que o sistema "pense" sem bloquear a escuta.

### 2. Área de Broca (Input/Output)
* **Listen (`listen.py`):**
    * Reconhecimento de fala via **Faster-Whisper** (Local).
    * Processamento de sinal com `numpy` e `noisereduce`.
    * **Intention Normalizer:** Filtra alucinações do Whisper e aplica correções fonéticas aprendidas (Memória de Reflexos).
* **Speak (`speak.py`):** Síntese de voz neural (Edge-TTS) e reprodução assíncrona.

### 3. Hipocampo (Memória)
* **Memória Episódica (`memoria.py`):** Banco vetorial (**ChromaDB**) para armazenar factos e conversas de longo prazo (RAG - Retrieval Augmented Generation).
* **Reflexos (`reflexos.py`):** Memória associativa rápida para corrigir erros fonéticos recorrentes (ex: "tocasho" -> "tocar").

### 4. Córtex Motor (Ação)
* **Launcher (`launcher.py`):** Indexador inteligente que varre o Menu Iniciar e localiza executáveis ou URIs (Spotify, Steam, URLs).
* **Agentes Especialistas:** Módulos de visão computacional (ex: Spotify Automation) e controlo de sistema.

---

## 🛠️ Stack Tecnológico

* **Core:** Python 3.10+
* **Arquitetura:** Event-Driven (Pub/Sub Pattern)
* **IA & NLP:**
    * Nuvem: `groq` (Llama 3.3 Versatile)
    * Local: `ollama` (Qwen 2 / Llama 3)
    * STT: `faster-whisper` (Substituindo Vosk/SpeechRecognition)
* **Banco de Dados:** `chromadb` (Vector Store)
* **Áudio:** `sounddevice` (Captura raw), `numpy`
* **Visão/Automação:** `opencv-python`, `pyautogui`

---

## 📂 Estrutura do Projeto

```text
J.A.R.V.I.S/
│
├── main.py                     # Kernel: Bootstrap e Injeção de Dependências
├── requirements.txt            # Dependências atualizadas
├── .env                        # Credenciais (GROQ_API_KEY, etc.)
│
├── data/                       # Persistência
│   ├── jarvis_memory_db/       # Banco de dados ChromaDB
│   └── speech_config.json      # Configurações de Hotwords e Reflexos
│
└── jarvis_system/              # Núcleo Modular
    │
    ├── protocol.py             # Definição de Contratos de Eventos
    │
    ├── cortex_frontal/
    │   ├── orchestrator.py     # Lógica de Fluxo e Atenção
    │   ├── brain_llm.py        # Gestor de LLMs (Híbrido)
    │   ├── event_bus.py        # Barramento de Eventos (Pub/Sub)
    │   └── observability.py    # Sistema de Logs Coloridos
    │
    ├── area_broca/
    │   ├── listen.py           # Whisper Service + VAD
    │   └── speak.py            # TTS Service
    │
    ├── hipocampo/
    │   ├── memoria.py          # Interface ChromaDB
    │   └── reflexos.py         # Aprendizado Rápido
    │
    └── cortex_motor/
        ├── launcher.py         # Indexador de Apps e Web
        └── tool_registry.py    # Registro de Ferramentas

🚀 Instalação e Configuração
1. Pré-requisitos
Python 3.10 ou superior.

Ollama instalado e rodando (para modo offline/fallback).

Chave de API da Groq.

2. Setup do Ambiente

# Clone o repositório
git clone [https://github.com/seu-usuario/jarvis-v2.git](https://github.com/seu-usuario/jarvis-v2.git)
cd jarvis-v2

# Crie o ambiente virtual
python -m venv .venv

# Ative o ambiente
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Instale as dependências
pip install -r requirements.txt

3. Configuração (.env)
Crie um arquivo .env na raiz:

GROQ_API_KEY=gsk_sua_chave_aqui
JARVIS_MODEL_CLOUD=llama-3.3-70b-versatile
JARVIS_MODEL_LOCAL=qwen2:0.5b

4. Execução
python main.py

🎮 Funcionalidades e Comandos
Modo Híbrido: Se a internet cair, o Jarvis avisa e muda para o modelo local (Ollama).

Memória Viva: "Jarvis, memorize que o código do portão é 1234".

Recuperação (RAG): "Qual é o código do portão?" (Busca no ChromaDB).

Aprendizado Ativo: Se ele entender errado, diga: "Aprenda que 'tocasho' significa 'tocar'". Ele guardará isso nos reflexos.

Apps: "Abrir Spotify", "Abrir VS Code", "Tocar 30PRAUM" (Spotify Agent).

⚠️ Solução de Problemas
Erro de Áudio (PortAudio): Se houver erro no sounddevice, verifique se o driver de microfone está definido como padrão no Windows.

Memória Offline: Se o ChromaDB falhar, o sistema inicia em modo "Amnésia" (apenas reativo).

Whisper Lento: A primeira execução baixa o modelo (~500MB). As seguintes são instantâneas.


### Principais Alterações Realizadas:

1.  **Atualização da Árvore de Arquivos:** Reflete a nova organização em `jarvis_system/` com a separação clara entre `cortex_frontal`, `area_broca`, etc.
2.  **Destaque ao Event Bus:** Documentei a mudança crucial para uma arquitetura orientada a eventos, que não existia na versão anterior.
3.  **Cérebro Híbrido:** Adicionei a explicação sobre o fallback entre Groq (Nuvem) e Ollama (Local), presente no código `brain_llm.py`.
4.  **Memória & Reflexos:** Detalhei o uso do `ChromaDB` e a funcionalidade de correção fonética dinâmica (Reflexos) encontrada em `listen.py` e `reflexos.py`.
5.  **Substituição de Bibliotecas:** Removi referências a `PyAudio` e `SpeechRecogn