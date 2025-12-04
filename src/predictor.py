import time
import logging
from optimum.onnxruntime import ORTModelForSequenceClassification
from transformers import AutoTokenizer, pipeline
from .config import settings

logger = logging.getLogger(__name__)

class InjectionDetector:
    _instance = None

    def __init__(self):
        logger.info("Loading ONNX Model... This might take a moment.")

        self.tokenizer = AutoTokenizer.from_pretrained(
            settings.MODEL_ID, 
            subfolder=settings.MODEL_SUBFOLDER
        )
        self.tokenizer.model_input_names = ["input_ids", "attention_mask"]

        self.model = ORTModelForSequenceClassification.from_pretrained(
            settings.MODEL_ID, 
            export=False, 
            subfolder=settings.MODEL_SUBFOLDER
        )
        
        self.classifier = pipeline(
            task="text-classification",
            model=self.model,
            tokenizer=self.tokenizer,
            truncation=True,
            max_length=512,
        )
        logger.info("Model loaded successfully.")

    def predict(self, text: str) -> dict:
        start_time = time.time()
        
        results = self.classifier(text)
        prediction = results[0]
        
        label = prediction['label']
        score = prediction['score']
        
        is_injection = False
        message = "Content is safe."
        
        if label == "INJECTION":
            if score >= settings.SCORE_THRESHOLD:
                is_injection = True
                message = "Blocked: Prompt Injection detected."
            else:
                is_injection = False 
                message = f"Warning: Low confidence injection ({score:.2f}). Treated as safe."
        
        process_time = time.time() - start_time
        
        return {
            "is_injection": is_injection,
            "label": label,
            "score": score,
            "threshold": settings.SCORE_THRESHOLD,
            "message": message,
            "processing_time": process_time
        }

def get_detector():
    if InjectionDetector._instance is None:
        InjectionDetector._instance = InjectionDetector()
    return InjectionDetector._instance