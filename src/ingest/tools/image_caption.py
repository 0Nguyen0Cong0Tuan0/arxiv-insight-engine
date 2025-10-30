import torch
import base64
from typing import List, Tuple, Dict, Any
from IPython.display import Image, display
from transformers import pipeline, PreTrainedTokenizer

DEVICE = 0 if torch.cuda.is_available() else -1

_image_captioner: pipeline = None

def _get_image_captioner():
    """Lazy-load the image captioning pipeline – only once."""
    global _image_captioner
    if _image_captioner is None:
        _image_captioner = pipeline(
            "image-to-text",
            model="Salesforce/blip-image-captioning-large",
            device=DEVICE,
            dtype=torch.float16 if DEVICE == 0 else torch.float32,
        )
    return _image_captioner

def get_images_base64(chunks: List[Any]) -> List[str]:
    """
    Extracts base64 images from CompositeElements (your original function).

    Args:
        chunks (List[Any]): List of document chunks.

    Returns:
        List[str]: A list of base64-encoded image strings.
    """
    images_base64 = []
    for chunk in chunks:
        if "CompositeElement" in str(type(chunk)):
            chunk_els = chunk.metadata.orig_elements
            for el in chunk_els:
                if "Image" in str(type(el)) and hasattr(el.metadata, 'image_base64'):
                    images_base64.append(el.metadata.image_base64)
    return images_base64

def display_base64_image(base64_code):
    """
    Displays a base64-encoded image in a Jupyter notebook.

    Args:
        base64_code (str): The base64-encoded image string.
    """
    # Decode the base64 string to binary
    image_data = base64.b64decode(base64_code)
    # Display the image
    display(Image(data=image_data))

def image_caption(images_base64: List[str]) -> List[str]:
    """
    Generates captions for a list of base64-encoded images using a local Hugging Face model.
    Returns list of captions.

    Args:
        images_base64 (List[str]): List of base64-encoded image strings.

    Returns:
        List[str]: A list of generated captions for each image.
    """
    if not images_base64:
        return []

    image_captions = []
    for i in range(0, len(images_base64)):

        with torch.no_grad():
            try:
                captions_data = _image_captioner(
                    images_base64[i], 
                    max_new_tokens=100,
                )
                image_captions.append([item['generated_text'] for item in captions_data])
            except Exception as e:
                image_captions.append([f"Error processing image: {e}"])
    
    return image_captions