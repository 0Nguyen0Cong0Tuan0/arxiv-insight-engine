from pathlib import Path
from unstructured.partition.pdf import partition_pdf
from typing import List

def extract_with_unstructured(pdf_path: str) -> List[List]:
    """
    Extracts text, tables, figures from PDF using unstructured.
    Returns dict with raw elements + HF-summarized versions.

    Args:
        pdf_path (str): Path to the PDF file.
        
    Returns:
        List containing all elements, text elements, and table elements.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    elements = partition_pdf(
        filename=pdf_path,
        extract_images_in_pdf=True,
        infer_table_structure=True,
        strategy="hi_res",
        languages=["eng"],
        extract_image_block_types=["Image", "Table"],
        extract_image_block_to_payload=True, 
        chunking_strategy="by_title",
        max_characters=10000,  
        combine_text_under_n_chars=2000,
        new_after_n_chars=6000,
        size={'longest_edge': 2048}
    )

    texts = [elem for elem in elements if "CompositeElement" in str(type(elem))]
    tables = [elem for elem in elements if "Table" in str(type(elem))]

    assert len(elements) == len(tables) + len(texts), "Some elements were neither text nor table."
    return [elements, texts, tables]