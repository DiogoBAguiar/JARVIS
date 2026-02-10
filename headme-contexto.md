# MANUAL DE CLASSIFICAÇÃO TAXONÔMICA - J.A.R.V.I.S.

Este documento define as regras estritas para a classificação de arquivos de áudio pelo Agente Bibliotecário. O objetivo é organizar os arquivos na estrutura de pastas correta baseando-se na semântica da frase.

## 1. CATEGORIAS DE PRIMEIRO NÍVEL (Pastas Raiz)

### **🛡️ SEGURANÇA E COMBATE**
* **ALERTA**: Perigo iminente. Emoção: `worried`, `shouting`, `tense`, `scared`, `panicked`.
* **COMBATE**: Protocolos ofensivos/defesa ativa. Emoção: `confident`, `angry`, `serious`, `furious`.
* **STEALTH**: Modos silenciosos/espionagem. Emoção: `whispering`, `soft tone`, `hesitating`.

### **⚠️ GESTÃO DE ERROS (Prioridade Alta)**
* **ERRO_PERMISSAO**: Acesso negado/sem privilégios. Emoção: `serious`, `stern`, `disapproving`.
* **ERRO_COMANDO**: Comando inválido/não compreendido. Emoção: `confused`, `apologetic`, `awkward`.
* **ERRO_SISTEMA**: Falhas críticas/crashes. Emoção: `worried`, `serious`, `anxious`.
* **STATUS_ERRO**: Falha operacional leve (wifi, download). Emoção: `regretful`, `neutral`, `upset`.

### **⚙️ OPERACIONAL E TÉCNICO**
* **SISTEMA**: Hardware, bateria, CPU. Emoção: `serious`, `professional`.
* **DADOS**: Processamento, downloads, análise. Emoção: `serious`, `speedy` (in a hurry tone).
* **ENGENHARIA**: Construção, código, manutenção. Emoção: `focused`, `confident`.
* **STATUS**: Relatório de estado (Online/Pronto). Emoção: `confident`, `satisfied`.

### **💬 INTERAÇÃO SOCIAL E PERSONALIDADE**
* **BOAS_VINDAS**: Saudações iniciais. Emoção: `happy`, `welcoming`, `excited`, `delighted`.
* **INTERACAO**: Prontidão, small talk ("Pois não?"). Emoção: `helpful`, `sincere`, `friendly`.
* **CONFIRMACAO**: Aceite de ordens ("Sim senhor"). Emoção: `confident`, `succinct`, `yielding`.
* **FORMAL**: Polidez extrema/mordomo. Emoção: `polite`, `elegant`, `sincere`.
* **PENSAMENTO**: Filler words ("Deixe-me ver..."). Emoção: `thoughtful`, `hesitating`.

### **🎭 PERSONALIDADE COMPLEXA**
* **HUMOR**: Piadas, ironia leve. Emoção: `amused`, `witty`, `laughing`, `chuckling`.
* **HUMOR_ERRO**: Sarcasmo sobre falhas ("Quebrei a internet"). Emoção: `awkward`, `amused`, `embarrassed`.
* **DARK**: Ameaçador, vilão, humor negro. Emoção: `low`, `mysterious`, `disdainful`, `scornful`.
* **FILOSOFIA**: Reflexões profundas. Emoção: `thoughtful`, `calm`, `sincere`.

## 2. LISTA OFICIAL DE EMOÇÕES PERMITIDAS (Use apenas estas tags em inglês)

**Emoções:**
`angry`, `sad`, `disdainful`, `excited`, `surprised`, `satisfied`, `unhappy`, `anxious`, `hysterical`, `delighted`, `scared`, `worried`, `indifferent`, `upset`, `impatient`, `nervous`, `guilty`, `scornful`, `frustrated`, `depressed`, `panicked`, `furious`, `empathetic`, `embarrassed`, `reluctant`, `disgusted`, `keen`, `moved`, `proud`, `relaxed`, `grateful`, `confident`, `interested`, `curious`, `confused`, `joyful`, `disapproving`, `negative`, `denying`, `astonished`, `serious`, `sarcastic`, `conciliative`, `comforting`, `sincere`, `sneering`, `hesitating`, `yielding`, `painful`, `awkward`, `amused`.

**Tom:**
`(in a hurry tone)`, `(shouting)`, `(screaming)`, `(whispering)`, `(soft tone)`.

**Especial:**
`(laughing)`, `(chuckling)`, `(sobbing)`, `(crying loudly)`, `(sighing)`, `(panting)`, `(groaning)`.

## 3. REGRAS DE CONTEXTO TEMPORAL
* **morning**: Se tiver "Bom dia".
* **afternoon**: Se tiver "Boa tarde".
* **night**: Se tiver "Boa noite".
* **any**: Padrão para tudo o resto.

## 4. REGRAS DE SUBCONTEXTO
* **query**: PERGUNTA ("Deseja algo?").
* **status**: ESTADO ("Bateria cheia").
* **alert**: AVISO ("Cuidado").
* **passive**: REAÇÃO CURTA ("Sim", "Não", "Pois não").
* **action**: AÇÃO ("Abrindo porta").
* **storytelling**: NARRATIVA LONGA.