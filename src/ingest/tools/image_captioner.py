import torch
import base64
from typing import List
from transformers import pipeline
from threading import Lock

from src.ingest.config import settings

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
            dtype=torch.float16 if self.device == 0 else torch.float32,
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






















# DEVICE = 0 if torch.cuda.is_available() else -1

# _image_captioner: pipeline = None

# def _get_image_captioner():
#     """Lazy-load the image captioning pipeline – only once."""
#     global _image_captioner
#     if _image_captioner is None:
#         _image_captioner = pipeline(
#             "image-to-text",
#             model="Salesforce/blip-image-captioning-large",
#             device=DEVICE,
#             dtype=torch.float16 if DEVICE == 0 else torch.float32,
#         )
#     return _image_captioner

# def get_images_base64(chunks: List[Any]) -> List[str]:
#     """
#     Extracts base64 images from CompositeElements (your original function).

#     Args:
#         chunks (List[Any]): List of document chunks.

#     Returns:
#         List[str]: A list of base64-encoded image strings.
#     """
#     images_base64 = []
#     for chunk in chunks:
#         if "CompositeElement" in str(type(chunk)):
#             chunk_els = chunk.metadata.orig_elements
#             for el in chunk_els:
#                 if "Image" in str(type(el)) and hasattr(el.metadata, 'image_base64'):
#                     images_base64.append(el.metadata.image_base64)
#     return images_base64

# def display_base64_image(base64_code):
#     """
#     Displays a base64-encoded image in a Jupyter notebook.

#     Args:
#         base64_code (str): The base64-encoded image string.
#     """
#     # Decode the base64 string to binary
#     image_data = base64.b64decode(base64_code)
#     # Display the image
#     display(Image(data=image_data))

# def image_caption(images_base64: List[str]) -> List[str]:
#     """
#     Generates captions for a list of base64-encoded images using a local Hugging Face model.
#     Returns list of captions.

#     Args:
#         images_base64 (List[str]): List of base64-encoded image strings.

#     Returns:
#         List[str]: A list of generated captions for each image.
#     """
#     if not images_base64:
#         return []

#     image_captions = []
#     for i in range(0, len(images_base64)):

#         with torch.no_grad():
#             try:
#                 captions_data = _image_captioner(
#                     images_base64[i], 
#                     max_new_tokens=100,
#                 )
#                 image_captions.append([item['generated_text'] for item in captions_data])
#             except Exception as e:
#                 image_captions.append([f"Error processing image: {e}"])
    
#     return image_captions