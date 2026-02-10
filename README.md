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

. (Raiz)
└── .gitignore
└── app.py
└── biblioteca_musical.txt
└── headme-contexto.md
└── inspect_chroma.py
└── msedgedriver.exe
└── README.md
└── requirements.txt
└── teste_renderizado.html
└── teste_renderizado_massivo.html
├── jarvis_system/
│   └── protocol.py
│   └── __init__.py
│   ├── agentes_especialistas/
│   │   └── agente_calendario.py
│   │   └── agente_clima.py
│   │   └── agente_media.py
│   │   └── agente_sistema.py
│   │   └── base_agente.py
│   │   └── __init__.py
│   │   ├── noticias/
│   │   │   ├── agent/
│   │   │   │   └── config.py
│   │   │   │   └── manager.py
│   │   │   ├── brain/
│   │   │   │   └── classifier.py
│   │   │   │   └── core.py
│   │   │   │   └── llm_setup_noticias.py
│   │   │   │   └── mocks.json
│   │   │   │   └── prompts.py
│   │   │   │   └── whatsapp_sender.py
│   │   │   ├── controller/
│   │   │   │   └── news_controller.py
│   │   │   ├── templates/
│   │   │   │   └── newspaper.html
│   │   │   ├── tools/
│   │   │   │   └── reporter.py
│   │   │   │   └── search_engine.py
│   │   │   │   └── sources.json
│   │   ├── spotify/
│   │   │   └── LEIA_ME_SPOTIFY.txt
│   │   │   └── __init__.py
│   │   │   ├── agent/
│   │   │   │   └── config.py
│   │   │   │   └── manager.py
│   │   │   │   └── __init__.py
│   │   │   ├── brain/
│   │   │   │   └── core.py
│   │   │   │   └── J.A.R.V.I.S.code-workspace
│   │   │   │   └── limbic_system.py
│   │   │   │   └── llm_setup.py
│   │   │   │   └── tools.py
│   │   │   │   └── __init__.py
│   │   │   ├── consciencia/
│   │   │   │   └── emotional_state.py
│   │   │   │   └── monitor.py
│   │   │   │   └── proprioception.py
│   │   │   │   └── vitals.py
│   │   │   │   └── __init__.py
│   │   │   ├── controller/
│   │   │   │   └── process_manager.py
│   │   │   │   └── spotify_controller.py
│   │   │   │   └── visual_navigator.py
│   │   │   │   └── __init__.py
│   │   │   ├── drivers/
│   │   │   │   └── page_model.py
│   │   │   │   └── scanner.py
│   │   │   │   └── setup_spotify_login.py
│   │   │   │   └── spotify_content.py
│   │   │   │   └── spotify_nav.py
│   │   │   │   └── spotify_player.py
│   │   │   │   └── spotify_selectors.py
│   │   │   │   └── web_driver.py
│   │   │   │   ├── estrategias/
│   │   │   │   │   └── search_engine.py
│   │   │   │   │   └── __init__.py
│   │   │   ├── img/
│   │   │   │   └── play_small_white.png
│   │   │   │   └── play_spotify.png
│   │   │   ├── input/
│   │   │   │   └── background.py
│   │   │   │   └── keyboard.py
│   │   │   │   └── manager.py
│   │   │   │   └── __init__.py
│   │   │   ├── strategies/
│   │   │   │   └── artist.py
│   │   │   │   └── filter_manager.py
│   │   │   │   └── playlist.py
│   │   │   │   └── track.py
│   │   │   │   └── __init__.py
│   │   │   ├── vision/
│   │   │   │   └── dependencies.py
│   │   │   │   └── finder.py
│   │   │   │   └── ocr.py
│   │   │   │   └── system.py
│   │   │   │   └── __init__.py
│   │   │   ├── window/
│   │   │   │   └── manager.py
│   │   │   │   └── win32_driver.py
│   │   │   │   └── __init__.py
│   ├── area_broca/
│   │   └── composer.py
│   │   └── fabrica_local.py
│   │   └── frases_padrao.py
│   │   └── __init__.py
│   │   ├── listen/
│   │   │   └── config.py
│   │   │   └── driver.py
│   │   │   └── main.py
│   │   │   └── transcriber.py
│   │   │   └── __init__.py
│   │   ├── model_en/
│   │   │   └── README
│   │   │   ├── am/
│   │   │   │   └── final.mdl
│   │   │   ├── conf/
│   │   │   │   └── mfcc.conf
│   │   │   │   └── model.conf
│   │   │   ├── graph/
│   │   │   │   └── disambig_tid.int
│   │   │   │   └── Gr.fst
│   │   │   │   └── HCLr.fst
│   │   │   │   ├── phones/
│   │   │   │   │   └── word_boundary.int
│   │   │   ├── ivector/
│   │   │   │   └── final.dubm
│   │   │   │   └── final.ie
│   │   │   │   └── final.mat
│   │   │   │   └── global_cmvn.stats
│   │   │   │   └── online_cmvn.conf
│   │   │   │   └── splice.conf
│   │   ├── model_pt/
│   │   │   └── disambig_tid.int
│   │   │   └── final.mdl
│   │   │   └── Gr.fst
│   │   │   └── HCLr.fst
│   │   │   └── mfcc.conf
│   │   │   └── phones.txt
│   │   │   └── README
│   │   │   └── word_boundary.int
│   │   │   ├── ivector/
│   │   │   │   └── final.dubm
│   │   │   │   └── final.ie
│   │   │   │   └── final.mat
│   │   │   │   └── global_cmvn.stats
│   │   │   │   └── online_cmvn.conf
│   │   │   │   └── splice.conf
│   │   ├── speak/
│   │   │   └── config.py
│   │   │   └── engine.py
│   │   │   └── indexer.py
│   │   │   └── main.py
│   │   │   └── synthesizer.py
│   │   │   └── __init__.py
│   ├── cortex_frontal/
│   │   └── curiosity.py
│   │   └── observability.py
│   │   └── voice_director.py
│   │   └── __init__.py
│   │   ├── brain_llm/
│   │   │   └── config.py
│   │   │   └── key_manager.py
│   │   │   └── main.py
│   │   │   └── prompt_factory.py
│   │   │   └── providers.py
│   │   │   └── __init__.py
│   │   ├── event_bus/
│   │   │   └── core.py
│   │   │   └── model.py
│   │   │   └── __init__.py
│   │   ├── orchestrator/
│   │   │   └── attention.py
│   │   │   └── cognition.py
│   │   │   └── config.py
│   │   │   └── learning.py
│   │   │   └── main.py
│   │   │   └── tools_handler.py
│   │   │   └── __init__.py
│   ├── cortex_motor/
│   │   └── launcher.py
│   │   └── os_actions.py
│   │   └── tool_registry.py
│   │   └── __init__.py
│   │   ├── camera/
│   │   │   └── spatial_memory.py
│   ├── cortex_visual/
│   │   └── config.py
│   │   └── eyes.py
│   │   └── face_id.py
│   │   └── main.py
│   │   └── __init__.py
│   ├── data/
│   │   └── (Conteúdo Omitido)
│   ├── front-end/
│   │   └── server.py
│   │   ├── templates/
│   │   │   └── index.html
│   ├── hipocampo/
│   │   └── limpar_memoria.py
│   │   └── __init__.py
│   │   ├── memoria/
│   │   │   └── connection.py
│   │   │   └── core.py
│   │   │   └── storage.py
│   │   │   └── __init__.py
│   │   ├── pensamento_musical/
│   │   │   └── core.py
│   │   │   └── enrichment.py
│   │   │   └── ingestion.py
│   │   │   └── maintenance.py
│   │   │   └── report.py
│   │   │   └── search.py
│   │   │   └── __init__.py
│   │   ├── reflexos/
│   │   │   └── core.py
│   │   │   └── fuzzy_logic.py
│   │   │   └── regex_compiler.py
│   │   │   └── storage.py
│   │   │   └── __init__.py
│   │   ├── subconsciente/
│   │   │   └── analyzer.py
│   │   │   └── aprendiz_voz.py
│   │   │   └── dreamer.py
│   │   │   └── log_reader.py
│   │   │   └── memory.py
│   │   │   └── __init__.py
│   ├── lobo_temporal/
│   │   └── __init__.py
│   ├── main/
│   │   └── api.py
│   │   └── core.py
│   │   └── __init__.py
│   ├── utils/
│   │   └── audio_ingestor.py
│   │   └── db_analyzer.py
│   │   └── repair_indexes.py
│   │   ├── cli_tools/
│   │   │   └── admin_music_console.py
│   │   ├── raw_audio/

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