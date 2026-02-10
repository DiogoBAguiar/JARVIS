import os
import shutil
import json
import re
from pathlib import Path
from typing import Optional, Literal, Dict
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# --- 1. HARDWARE CONSTRAINT ---
os.environ["CUDA_VISIBLE_DEVICES"] = ""

from agno.agent import Agent
from agno.models.groq import Groq 

# --- CONFIGURAÇÕES ---
load_dotenv()

BASE_DIR = Path(os.getcwd())
RAW_AUDIO_DIR = BASE_DIR / "jarvis_system" / "utils" / "raw_audio"
ASSETS_DIR = BASE_DIR / "jarvis_system" / "data" / "voices" / "assets"
INDEX_PATH = BASE_DIR / "jarvis_system" / "data" / "voices" / "voice_index.json"
CONTEXT_MD_PATH = BASE_DIR / "headme-contexto.md"

if not os.getenv("GROQ_API_KEY"):
    raise ValueError("❌ ERRO: A variável GROQ_API_KEY não foi encontrada no .env")

# --- 2. MODELO DE DADOS BLINDADO ---
class ClassificacaoAudio(BaseModel):
    # ATUALIZADO COM TODAS AS CATEGORIAS DA SUA IMAGEM
    category: Literal[
        'ALERTA', 'COMBATE', 'STEALTH', 
        'ERRO_PERMISSAO', 'ERRO_COMANDO', 'ERRO_SISTEMA', 'STATUS_ERRO', 
        'SISTEMA', 'DADOS', 'ENGENHARIA', 'STATUS', 
        'BOAS_VINDAS', 'INTERACAO', 'CONFIRMACAO', 'FORMAL', 'PENSAMENTO', 
        'HUMOR', 'HUMOR_ERRO', 'DARK', 'FILOSOFIA'
    ] = Field(..., description="A categoria exata em MAIÚSCULAS.")
    
    context: Literal['morning', 'afternoon', 'night', 'any'] = Field(..., description="O contexto temporal.")
    
    # Subcontextos sugeridos, mas permitindo string livre para flexibilidade (ex: storytelling)
    sub_context: str = Field(..., description="A intenção ou subcontexto em minúsculas (ex: query, status, alert, passive, action, storytelling).")
    
    emotion: str = Field(..., description="A emoção sugerida (tags da Fish Audio em inglês). Ex: serious, happy, whispering.")
    
    reasoning: str = Field(..., description="Justificativa breve.")

class AudioLibrarian:
    def __init__(self):
        self.context_rules = self._ler_regras_contexto()
        self.contadores_globais = self._inicializar_contadores()
        
        self.model = Groq(id="llama-3.3-70b-versatile")

        # Define esquema JSON para prompt manual
        self.schema_json = json.dumps(ClassificacaoAudio.model_json_schema())

        self.agent = Agent(
            model=self.model,
            description="Você é o bibliotecário-chefe do sistema J.A.R.V.I.S.",
            instructions=[
                "Classifique o áudio com base no nome do arquivo ou conteúdo do texto.",
                "Siga as regras de contexto do arquivo fornecido.",
                
                # --- INJEÇÃO DE CONTEXTO FAMILIAR (NOVO) ---
                "--- CONTEXTO DE ENTIDADES E FAMÍLIA ---",
                "1. Diogo (Eu): Usuário principal, núcleo operacional.",
                "2. Rodrigo: Pai (Referência de estabilidade).",
                "3. Suênia: Mãe (Núcleo emocional).",
                "4. Caio: Irmão (Força em expansão).",
                "5. Bruna: Irmã (Convergência sensibilidade/força).",
                
                "--- REGRA ESPECIAL DE DADOS/BIOS ---",
                "Se o texto for uma descrição, biografia ou perfil sobre essas pessoas:",
                "-> CATEGORIA: DADOS",
                "-> SUB_CONTEXT: storytelling",
                "-> EMOÇÃO: respectful, serious ou confident.",
                # -------------------------------------------

                "Use APENAS as categorias permitidas.",
                "Traduza a intenção para a emoção correta em inglês (ex: 'Sério' -> 'serious').",
                "RESPONDA APENAS COM JSON VÁLIDO seguindo o esquema.",
                f"Schema: {self.schema_json}"
            ],
            markdown=False
        )
        
        print(f"🖥️  AudioLibrarian Online.")
        print(f"📊 Contadores Carregados: {len(self.contadores_globais)} categorias.")
        print(f"📥 Zona de Entrega: {RAW_AUDIO_DIR}")

    def _ler_regras_contexto(self) -> str:
        if CONTEXT_MD_PATH.exists():
            with open(CONTEXT_MD_PATH, "r", encoding="utf-8") as f:
                return f.read()
        return "Regras padrão..."

    def _inicializar_contadores(self) -> Dict[str, int]:
        contadores = {}
        if INDEX_PATH.exists():
            try:
                with open(INDEX_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item_id, metadata in data.items():
                        cat = metadata.get('category', '').lower()
                        match = re.search(r'(\d+)$', str(metadata.get('id', '')))
                        if match and cat:
                            numero = int(match.group(1))
                            if numero > contadores.get(cat, 0):
                                contadores[cat] = numero
            except Exception as e:
                print(f"⚠️ Erro ao ler índices: {e}")
        return contadores

    def _get_proximo_id(self, categoria: str) -> str:
        cat_lower = categoria.lower()
        atual = self.contadores_globais.get(cat_lower, 0)
        proximo = atual + 1
        self.contadores_globais[cat_lower] = proximo
        return f"{cat_lower}_{proximo:02d}"

    def _normalizar_hash(self, texto: str) -> str:
        texto = re.sub(r'\([^)]*\)', '', texto) 
        texto = texto.lower()
        trans = str.maketrans("áàãâéêíóõôúç", "aaaaeeiooouc")
        texto = texto.translate(trans)
        return re.sub(r'[^a-z0-9]', '', texto)

    def processar_fila(self):
        if not RAW_AUDIO_DIR.exists():
            os.makedirs(RAW_AUDIO_DIR)
            print(f"📁 Pasta criada: {RAW_AUDIO_DIR}")
            return

        arquivos = [f for f in os.listdir(RAW_AUDIO_DIR) if f.endswith(".mp3")]
        
        if not arquivos:
            print("💤 Fila vazia.")
            return

        print(f"🚀 Processando {len(arquivos)} arquivos...")

        indice = {}
        if INDEX_PATH.exists():
            try:
                with open(INDEX_PATH, 'r', encoding='utf-8') as f:
                    indice = json.load(f)
            except: pass

        count_sucesso = 0

        for arquivo in arquivos:
            # Substitui _ por espaço para a IA ler melhor
            frase_limpa = os.path.splitext(arquivo)[0].replace("_", " ")
            print(f"\n🎧 Analisando: '{frase_limpa[:50]}...'") # Mostra só o começo para não poluir
            
            try:
                # 1. Classificação via Groq
                response = self.agent.run(f"Classifique: '{frase_limpa}'\nREGRAS:\n{self.context_rules}")
                conteudo_limpo = response.content.replace("```json", "").replace("```", "").strip()
                
                # Validação Manual Pydantic
                resultado = ClassificacaoAudio.model_validate_json(conteudo_limpo)
                
                # 2. Dados Definidos
                cat = resultado.category.upper()
                ctx = resultado.context
                sub = resultado.sub_context.lower()
                
                # 3. Geração de ID Inteligente
                novo_id_formatado = self._get_proximo_id(cat)
                novo_nome_arquivo = f"{novo_id_formatado}.mp3"
                
                print(f"   🧠 Raciocínio: {resultado.reasoning}")
                print(f"   🏷️  Tag: [{cat} | {ctx} | {sub}]")
                print(f"   🔢 ID Gerado: {novo_id_formatado}")

                # 4. Destino
                destino_dir = ASSETS_DIR / cat / ctx / sub
                destino_dir.mkdir(parents=True, exist_ok=True)
                caminho_final = destino_dir / novo_nome_arquivo
                
                # 5. Movimentação
                shutil.move(str(RAW_AUDIO_DIR / arquivo), str(caminho_final))
                
                # 6. Atualização Índice
                chave_hash = self._normalizar_hash(frase_limpa)
                path_relativo = f"assets/{cat}/{ctx}/{sub}/{novo_nome_arquivo}"
                
                novo_registro = {
                    "id": novo_id_formatado,
                    "text": frase_limpa,
                    "file_path": path_relativo,
                    "category": cat,
                    "key_hash": chave_hash,
                    "context": ctx,
                    "sub_context": sub,
                    "emotion": resultado.emotion
                }
                
                indice[chave_hash] = novo_registro
                print(f"   ✅ Movido para: {path_relativo}")
                count_sucesso += 1

            except Exception as e:
                print(f"   ❌ Erro: {e}")

        # Salva JSON
        with open(INDEX_PATH, 'w', encoding='utf-8') as f:
            json.dump(indice, f, indent=4, ensure_ascii=False)
        
        print(f"\n✨ Concluído! {count_sucesso}/{len(arquivos)} organizados.")

if __name__ == "__main__":
    librarian = AudioLibrarian()
    librarian.processar_fila()