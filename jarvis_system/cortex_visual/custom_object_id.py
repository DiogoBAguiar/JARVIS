import os
import cv2
import torch
import numpy as np
import torchvision.transforms as transforms
from torchvision.models import mobilenet_v2, MobileNet_V2_Weights
import torch.nn.functional as F
from jarvis_system.cortex_frontal.observability import JarvisLogger

log = JarvisLogger("VISUAL_CUSTOM_OBJ")

class CustomObjectRecognizer:
    def __init__(self):
        log.info("🧠 Inicializando Motor de Reconhecimento de Objetos Customizados...")
        
        # 1. Carrega o modelo MobileNetV2 e remove a camada de classificação 
        # (Queremos apenas extrair características, não prever classes padrão)
        weights = MobileNet_V2_Weights.DEFAULT
        self.model = mobilenet_v2(weights=weights)
        self.model.classifier = torch.nn.Identity()
        self.model.eval()

        # Usa a placa de vídeo MX110 (CUDA) se disponível
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

        # Prepara a imagem para o formato que a IA gosta (224x224, normalizada)
        self.preprocess = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        self.known_embeddings = []
        self.known_names = []
        
        # Caminho da memória
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.memory_path = os.path.abspath(os.path.join(current_dir, "..", "data", "object_memory"))
        
        self._load_memory()

    def _load_memory(self):
        """Carrega e estuda as fotos dos objetos nas pastas."""
        if not os.path.exists(self.memory_path):
            try: os.makedirs(self.memory_path)
            except: pass
            return

        objetos_treinados = 0
        for item in os.listdir(self.memory_path):
            obj_path = os.path.join(self.memory_path, item)
            
            if os.path.isdir(obj_path):
                nome_objeto = item.replace("_", " ").title()
                fotos = [f for f in os.listdir(obj_path) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
                
                if not fotos: continue
                log.info(f"📸 Treinando reconhecimento de: [{nome_objeto}] com {len(fotos)} fotos...")
                
                for foto in fotos:
                    img_path = os.path.join(obj_path, foto)
                    img = cv2.imread(img_path)
                    if img is not None:
                        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        embedding = self.get_embedding(rgb_img)
                        self.known_embeddings.append(embedding)
                        self.known_names.append(nome_objeto)
                
                objetos_treinados += 1
                
        log.info(f"✅ Memória de Objetos carregada: {objetos_treinados} objetos personalizados.")

    def get_embedding(self, rgb_image):
        """Gera a assinatura matemática do objeto."""
        input_tensor = self.preprocess(rgb_image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            embedding = self.model(input_tensor)
        return embedding

    def identify(self, rgb_crop):
        """Compara o recorte da câmara com o banco de dados."""
        if not self.known_embeddings:
            return None

        # Pega a assinatura do objeto que está na câmara agora
        target_emb = self.get_embedding(rgb_crop)
        
        melhor_similaridade = -1.0
        melhor_nome = None

        # Compara com tudo o que ele sabe
        for known_emb, name in zip(self.known_embeddings, self.known_names):
            sim = F.cosine_similarity(target_emb, known_emb).item()
            if sim > melhor_similaridade:
                melhor_similaridade = sim
                melhor_nome = name

        # Tolerância de Similaridade (0.75 a 0.85 é o ideal para a MobileNet)
        if melhor_similaridade > 0.82: 
            return melhor_nome
            
        return None