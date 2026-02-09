# 📂 Estrutura de Contextos de Voz - J.A.R.V.I.S.

Este diretório armazena os arquivos de áudio gerados pela Fish Audio. A organização segue uma hierarquia lógica para facilitar a escolha dinâmica de frases pelo sistema.

## 📍 Hierarquia de Pastas
Os arquivos são organizados da seguinte forma:

`assets / CATEGORIA / contexto_temporal / sub_contexto / arquivo.mp3`

### Exemplo Real:
> `assets/BOAS_VINDAS/night/query/boas_vindas_03.mp3`
> *(Categoria: Boas Vindas | Tempo: Noite | Intenção: Perguntar o que fazer)*

---

## 🏷️ Legenda de Definições

### 1. Categorias (Nível 1)
As grandes áreas de atuação do sistema.
- **BOAS_VINDAS**: Frases de inicialização ou retorno.
- **ALERTA**: Avisos de perigo, erro ou intrusão.
- **COMBATE**: Frases ofensivas ou defensivas.
- **GENERICO**: Respostas comuns (sim, não, aguarde).

### 2. Contexto Temporal (Nível 2)
Define o momento do dia para a frase fazer sentido.
- **morning**: Madrugada e Manhã.
- **afternoon**: Tarde.
- **night**: Noite.
- **any**: Funciona em qualquer horário (atemporal).

### 3. Sub-Contextos / Intenção (Nível 3)
Define o *objetivo* ou o *tom* da frase. É aqui que a "personalidade" se refina.

| Sub-Contexto | Definição | Exemplo Típico |
| :--- | :--- | :--- |
| **`boot`** | **Inicialização**. O sistema está ligando pela primeira vez ou reiniciando. É uma apresentação. | *"Jarvis Online."* |
| **`return`** | **Retorno**. O usuário estava ausente e voltou. Foca na reconexão. | *"Bem-vindo de volta, senhor."* |
| **`query`** | **Pergunta Ativa**. O sistema toma a iniciativa e pergunta qual é a ordem. | *"O que deseja fazer hoje?"* |
| **`status`** | **Relatório**. Informativo, foca em dizer que os sistemas estão operacionais. | *"Sistemas estáveis e prontos."* |
| **`passive`** | **Passivo/Serviçal**. Resposta curta e obediente quando chamado pelo nome. | *"Às ordens."* / *"Pronto."* |
| **`alert`** | **Aviso Crítico**. Usado em categorias de ALERTA. | *"Intrusão detectada!"* |

---

## ⚠️ Regras de Manutenção
1. **Nomes de Arquivo**: Devem seguir o padrão `id_do_json.mp3` (ex: `boas_vindas_05.mp3`).
2. **JSON Mestre**: Todo arquivo aqui DEVE ter uma entrada correspondente no `voice_index.json` na raiz de `voices/`.
3. **Mover Arquivos**: Se mover um arquivo de pasta, atualize o caminho (`file_path`) no JSON imediatamente.