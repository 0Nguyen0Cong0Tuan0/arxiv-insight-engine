import torch
from typing import List, Tuple, Dict, Any
from transformers import pipeline, PreTrainedTokenizer
from langchain.text_splitter import RecursiveCharacterTextSplitter

_summarizer: pipeline = None
_tokenizer: PreTrainedTokenizer = None

DEVICE = 0 if torch.cuda.is_available() else -1

def _get_summarizer():
    """Lazy-load the pipeline – only once."""
    global _summarizer
    if _summarizer is None:
        _summarizer = pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            device=DEVICE,
            dtype=torch.float16 if DEVICE == 0 else torch.float32,
        )
        _summarizer.tokenizer.model_max_length = 1024
        _tokenizer = _summarizer.tokenizer
    return _summarizer, _tokenizer

def _chunk_text(text: str, chunk_size: int = 4000, chunk_overlap: int = 100) -> List[str]:
    """
    Splits a long string into overlapping chunks that fit BART's 1024-token limit.

    Args:
        text (str): The input text to be chunked.
        chunk_size (int): The maximum size of each chunk.
        chunk_overlap (int): The number of overlapping characters between chunks.

    Returns:
        List[str]: A list of text chunks.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    return splitter.split_text(text)

def _gen_kwargs(
    input_text: str,
    tokenizer: PreTrainedTokenizer,
    base_max: int = 200,
    base_min: int = 30,
) -> Dict[str, int]:
    """
    Returns `max_length` and `min_length` based on TOKEN length.
    - Ensures max_length never exceeds input token length.

    Args:
        input_text (str): The text to be summarized.
        tokenizer (PreTrainedTokenizer): The tokenizer used to count tokens.
        base_max (int): The base maximum length for the summary.
        base_min (int): The base minimum length for the summary.

    Returns:
        Dict[str, int]: A dictionary with 'max_length' and 'min_length' keys
    """
    token_ids = tokenizer(input_text, truncation=False)["input_ids"]
    token_length = len(token_ids)

    if token_length == 0:
        return {"max_length": base_min, "min_length": 0}

    desired_max = max(base_min, token_length // 2)

    model_max_length = tokenizer.model_max_length
    max_len = min(base_max, desired_max, model_max_length, token_length)

    min_len = min(base_min, max_len)

    if token_length < base_min:
         min_len = token_length
         max_len = token_length

    return {"max_length": max_len, "min_length": min_len}

def summarize(
    texts: List[Any],
    tables: List[Any],
    max_input_chars: int = 2000,
    base_max_length: int = 200,
    base_min_length: int = 30,
) -> Tuple[List[str], List[str]]:
    """
    Summarises text and table elements.

    Args:
        texts (List[Any]): List of text elements to summarize.
        tables (List[Any]): List of table elements to summarize.
        max_input_chars (int): Maximum number of characters per input chunk.
        base_max_length (int): Base maximum length for summaries.
        base_min_length (int): Base minimum length for summaries.
    
    Returns:
        Tuple[List[str], List[str]]: Summaries for text and table elements.
    """
    # ------------------- TEXT -------------------
    raw_texts = [
        getattr(elem, "text", "").strip()
        for elem in texts
        if getattr(elem, "text", "").strip()
    ]
    text_summaries: List[str] = []

    for raw in raw_texts:
        chunks = _chunk_text(raw, chunk_size=max_input_chars, chunk_overlap=100)

        for chunk in chunks:
            if not chunk.strip():
                continue

            gen_kwargs = _gen_kwargs(chunk, _tokenizer, base_max_length, base_min_length)

            with torch.no_grad():
                out = _summarizer(
                    chunk,
                    **gen_kwargs,
                    do_sample=False,
                    truncation=True,
                )
            text_summaries.append(out[0]["summary_text"])

    # ------------------- TABLES (HTML) -------------------
    raw_htmls = [
        getattr(elem.metadata, "text_as_html", "").strip()
        for elem in tables
        if hasattr(elem, "metadata") and getattr(elem.metadata, "text_as_html", "")
    ]
    table_summaries: List[str] = []

    for raw in raw_htmls:
        chunks = _chunk_text(raw, chunk_size=max_input_chars, chunk_overlap=100)

        for chunk in chunks:
            if not chunk.strip():
                continue

            gen_kwargs = _gen_kwargs(chunk, base_max_length, base_min_length)

            with torch.no_grad():
                out = _summarizer(
                    chunk,
                    **gen_kwargs,
                    do_sample=False,
                    truncation=True,
                )
            table_summaries.append(out[0]["summary_text"])

    return text_summaries, table_summaries