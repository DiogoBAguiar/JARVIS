from ultralytics import YOLO
import cv2
import logging

log = logging.getLogger("VISUAL_OBJECTS")

class ObjectDetector:
    def __init__(self):
        self.model = YOLO("yolov8n.pt")
        
        # Objetos genéricos que o YOLO já conhece
        self.objetos_interesse = [
            'cell phone', 'laptop', 'cup', 'bottle', 'book', 'keyboard', 'mouse'
        ]
        
        # --- CARREGA O RECONHECEDOR CUSTOMIZADO ---
        self.custom_recognizer = None
        try:
            from .custom_object_id import CustomObjectRecognizer
            self.custom_recognizer = CustomObjectRecognizer()
        except Exception as e:
            log.error(f"Falha ao carregar reconhecedor de objetos customizados: {e}")

    def processar(self, frame):
        resultados = self.model(frame, device=0, verbose=False)
        objetos_finais = []

        for r in resultados:
            for box in r.boxes:
                classe_id = int(box.cls[0])
                nome_yolo = self.model.names[classe_id]
                confianca = float(box.conf[0])
                
                # O YOLO detetou algo que nos interessa (mesmo que ele ache que é um telemóvel)
                if confianca > 0.50 and nome_yolo in self.objetos_interesse:
                    nome_final = nome_yolo
                    
                    # 1. RECORTAR A IMAGEM DO OBJETO
                    # Pega as coordenadas exatas da caixa que o YOLO desenhou
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    # Garantir que as coordenadas não saem fora do ecrã
                    h, w, _ = frame.shape
                    y1, y2 = max(0, y1), min(h, y2)
                    x1, x2 = max(0, x1), min(w, x2)
                    
                    # Cria o recorte
                    recorte = frame[y1:y2, x1:x2]
                    
                    # 2. PERGUNTAR AO NOSSO MOTOR CUSTOMIZADO SE ELE CONHECE ISTO
                    if self.custom_recognizer and recorte.size > 0:
                        rgb_recorte = cv2.cvtColor(recorte, cv2.COLOR_BGR2RGB)
                        nome_customizado = self.custom_recognizer.identify(rgb_recorte)
                        
                        if nome_customizado:
                            # O MOTOR RECONHECEU! Ignoramos o YOLO e usamos o nosso nome.
                            nome_final = nome_customizado
                        else:
                            # Se não conhecemos, traduzimos o nome genérico do YOLO
                            traducao = {
                                'cell phone': 'CELULAR', 'laptop': 'NOTEBOOK', 
                                'cup': 'COPO', 'bottle': 'GARRAFA', 
                                'book': 'LIVRO', 'keyboard': 'TECLADO'
                            }
                            nome_final = traducao.get(nome_final, nome_final.upper())

                    objetos_finais.append(nome_final)

        return list(set(objetos_finais))