import os
import logging
import re
from pathlib import Path
from fishaudio import FishAudio
from fishaudio.utils import save

# =========================
# CONFIGURAÇÃO PROFISSIONAL
# =========================

API_KEY = os.getenv("FISHAUDIO_API_KEY") or "9f5ecc9c246a47079efd22d45ceff22b"
VOICE_ID = "a5b93aeddcc948c19ea04f0afe9d178c"

BASE_DIR = Path("jarvis_system/area_broca/voice_bank_fish")

# =========================
# MAPEAMENTO OFICIAL (EMOÇÃO & TOM)
# =========================
# Baseado na documentação oficial do Fish Audio S1
CONFIG_EMOCOES = {
    # Categoria Jarvis   Tag Oficial (Documentação)
    "neutro":      "(confident)",        # Padrão Jarvis: Seguro e firme
    "pergunta":    "(curious)",          # Entonação de dúvida
    "suspenso":    "(serious)",          # Pausa dramática/Sério
    "exclamacao":  "(excited)",          # Surpreso/Animado
    "urgente":     "(in a hurry tone)",  # TOM: Apressado (Velocidade e Urgência)
    "calmo":       "(soft tone)",        # TOM: Suave (Melhor que relaxed)
    "agressivo":   "(angry)",            # Emoção: Combate/Defesa
    "projetado":   "(shouting)",         # TOM: Voz projetada/Grito
    "sussurro":    "(whispering)",       # TOM: Sussurro real (Stealth)
    "robotico":    "(indifferent)",      # Emoção: Sem alma/Leitura fria
    "feliz":       "(satisfied)",        # Emoção: Sutilmente contente
    "autoritario": "(serious)"           # Emoção: Comando firme
}

PALAVRAS_CHAVE = [
    # --- 1. TEOLOGIA & ESPIRITUALIDADE ---
    "deus", "senhor", "jesus", "cristo", "espírito", "santo", "fé", "amor",
    "verdade", "vida", "luz", "salvação", "justiça", "misericórdia",
    "graça", "perdão", "aliança", "paz", "esperança", "glória",
    "reino", "céu", "terra", "coração", "alma", "palavra", "lei",
    "profeta", "apóstolo", "discípulo", "igreja", "povo",
    "oração", "jejum", "sacrifício", "promessa", "caminho",
    "mandamento", "sabedoria", "conhecimento", "temor",
    "bênção", "maldição", "redenção", "vida_eterna", "arrependimento",
    "pecado", "justificado", "santificado", "ressurreição",

    # --- 2. IDENTIDADE ---
    "jarvis", "olá", "senhora", "mestre", "chefe", "usuário",
    "operador", "comandante", "doutor", "você", "eu", "nós",

    # --- 3. SEGURANÇA ---
    "acesso", "negado", "autorizado", "permitido", "bloqueado", "liberado",
    "protocolo", "segurança", "código", "senha", "nível", "credencial",
    "biometria", "verificação", "validação", "firewall",

    # --- 4. STATUS & PROCESSOS ---
    "ativado", "desativado", "ativar", "desativar",
    "iniciando", "encerrando", "aguarde", "concluído", "executando",
    "processando", "analisando", "calculando", "buscando",
    "otimizando", "monitorando", "preparando", "simulando",
    "erro", "falha", "crítico", "alerta", "instável", "resolvido",

    # --- 5. HARDWARE ---
    "sistemas", "online", "offline", "servidor", "rede", "conexão",
    "bateria", "energia", "dados", "arquivo", "memória",
    "processador", "núcleo", "cache", "latência", "backup",

    # --- 6. INTERAÇÃO ---
    "sim", "não", "talvez", "entendido", "obrigado", "por_favor", "certo",
    "positivo", "negativo", "confirmado", "cancelado", "pronto", 
    "aguardando", "resposta", "pergunta", "dúvida", "suspenso", "exclamação",

    # --- 7. CONECTIVOS ---
    "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
    "e", "para", "com", "sem", "sobre", "entre", "por",
    "o", "a", "os", "as", "um", "uma", "uns", "umas", 

    # --- 8. TEMPO ---
    "segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo",
    "janeiro", "fevereiro", "março", "abril", "maio", "junho", 
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
    "manhã", "tarde", "noite", "madrugada", "meio_dia", "meia_noite",

    # --- 9. NÚMEROS & MEDIDAS ---
    "vinte", "trinta", "quarenta", "cinquenta", "sessenta", 
    "setenta", "oitenta", "noventa", "milhão", "bilhão",
    "porcento", "graus", "celsius", "fahrenheit", "volts", "watts", "amperes",
    "hertz", "decibéis", "pixels", "metros", "quilômetros", "milhas",
    "megabytes", "gigabytes", "terabytes", "bytes", "bits",

    # --- 10. AÇÕES DE SISTEMA ---
    "reiniciar", "atualizar", "baixar", "carregar", "instalar", "desinstalar",
    "configurar", "escanear", "rastrear", "localizar", "codificar", "decodificar",
    "copiar", "colar", "recortar", "apagar", "salvar", "abrir", "fechar",
    "aumentar", "diminuir", "mutar", "tocar", "pausar",

    # --- 11. INTERFACE ---
    "email", "mensagem", "chamada", "calendário", "relógio", "alarme", 
    "navegador", "janela", "aba", "pasta", "ícone", "área_de_trabalho",
    "volume", "brilho", "tela", "monitor", "camera", "microfone",
    "wifi", "bluetooth", "usb", "hdmi", "mouse", "teclado",

    # --- 12. CORES & ALFABETO ---
    "vermelho", "verde", "azul", "amarelo", "laranja", "roxo", "branco", "preto",
    "claro", "escuro", "transparente", "opaco", "sólido",
    "cheio", "vazio", "metade", "baixo", "alto", "médio",
    "alfa", "bravo", "charlie", "delta", "echo", "foxtrot", "tango", "zulu", "omega",

    # --- 13. CONTAGEM ---
    "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove", "dez", 
    "zero", "onze", "doze", "treze", "quatorze", "quinze", "dezesseis", "dezessete", "dezoito", "dezenove",
    "vinte", "trinta", "quarenta", "cinquenta", "sessenta", "setenta", "oitenta", "noventa", "cem",
    "duzentos", "trezentos", "quatrocentos", "quinhentos", "seiscentos", "setecentos", "oitocentos", "novecentos", "mil"
]

# =========================
# LOGGING
# =========================
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger("JARVIS-VOICE-FINAL")

def preparar_prompt(palavra: str, tag_oficial: str) -> str:
    """
    Constrói o prompt seguindo a regra: (tag) Texto
    Removemos pontuação extra que estava causando bugs.
    """
    # 1. Limpeza
    texto_limpo = palavra.strip().replace("_", " ").lower()
    
    # 2. Correção de Pronúncia (J.A.R.V.I.S -> Jarvis)
    texto_limpo = texto_limpo.replace("j.a.r.v.i.s", "jarvis")
    texto_limpo = texto_limpo.replace("j.a.r.v.i.s.", "jarvis")
    
    # 3. Capitalização
    texto_capitalizado = texto_limpo.capitalize()
    
    # 4. Prompt Limpo (Sem caracteres especiais colados no final)
    # A documentação diz: "Emotion tags MUST go at the beginning"
    return f"{tag_oficial} {texto_capitalizado}"

def iniciar_matriz_completa():
    log.info("🚀 Iniciando Geração Final J.A.R.V.I.S (Tags Oficiais + Tons)")
    log.info(f"   Palavras: {len(PALAVRAS_CHAVE)} | Variações: {len(CONFIG_EMOCOES)}")

    client = FishAudio(api_key=API_KEY)

    total_gerado = 0
    total_pulado = 0

    for palavra in PALAVRAS_CHAVE:
        pasta = BASE_DIR / palavra
        pasta.mkdir(parents=True, exist_ok=True)

        log.info(f"📂 Processando: {palavra.upper()}")

        for nome_arquivo, tag_oficial in CONFIG_EMOCOES.items():
            caminho = pasta / f"{nome_arquivo}.mp3"

            # Se quiser regravar TUDO para corrigir os bugs, remova este bloco IF
            if caminho.exists():
                total_pulado += 1
                continue

            # Gera o prompt
            texto_prompt = preparar_prompt(palavra, tag_oficial)
            
            # Log para conferência visual
            log.info(f"   🎙️  {nome_arquivo:<12} -> '{texto_prompt}'")

            try:
                audio = client.tts.convert(
                    text=texto_prompt,
                    reference_id=VOICE_ID,
                    format="mp3"
                )
                save(audio, caminho)
                total_gerado += 1

            except Exception as e:
                log.error(f"❌ Falha ao gerar '{palavra}:{nome_arquivo}' → {e}")

    log.info("="*30)
    log.info("✅ FINALIZADO")
    log.info(f"   Novos arquivos: {total_gerado}")
    log.info(f"   Pulados (já existiam): {total_pulado}")

if __name__ == "__main__":
    iniciar_matriz_completa()