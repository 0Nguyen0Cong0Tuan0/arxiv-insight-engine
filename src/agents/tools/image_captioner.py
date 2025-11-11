import torch
import base64
from typing import List
from transformers import pipeline
from threading import Lock

from config import settings

class ImageCaptioner:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Initialize the image captioning pipeline.
        """
        self.device = 0 if torch.cuda.is_available() else -1
        self.pipe = pipeline(
            "image-to-text",
            model=settings.CAPTIONER_MODEL,
            device=self.device,
            torch_dtype=torch.float16 if self.device == 0 else torch.float32,
        )

    def extract_base64_images(self, elements: List) -> List[str]:
        images = []
        for elem in elements:
            if "CompositeElement" in str(type(elem)):
                for sub in elem.metadata.orig_elements:
                    if "Image" in str(type(sub)) and hasattr(sub.metadata, 'image_base64'):
                        images.append(sub.metadata.image_base64)
        return images

    def caption_images(self, images_base64: List[str]) -> List[str]:
        if not images_base64:
            return []
        captions = []
        for b64 in images_base64:
            try:
                with torch.no_grad():
                    result = self.pipe(b64, max_new_tokens=100)
                    captions.append(result[0]["generated_text"])
            except Exception as e:
                captions.append(f"Error: {e}")
        return captions