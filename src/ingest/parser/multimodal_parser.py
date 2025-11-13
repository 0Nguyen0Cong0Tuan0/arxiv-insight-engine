from pathlib import Path
from unstructured.partition.pdf import partition_pdf
from typing import List, Tuple

def parse_pdf(pdf_path: str) -> Tuple[List, List, List]:
    """
    Extracts text, tables, figures from PDF using unstructured.
    Returns dict with raw elements + HF-summarized versions.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    elements = partition_pdf(
        filename=str(pdf_path),
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

    return elements