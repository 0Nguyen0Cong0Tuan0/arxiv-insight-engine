import torch
from typing import List, Dict, Optional
from transformers import pipeline
from langchain_text_splitters import RecursiveCharacterTextSplitter
from threading import Lock #  for thread safety

from config import settings

class Summarizer:
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
        Initialize the summarization pipeline and tokenizer.
        """
        self.device = 0 if torch.cuda.is_available() else -1
        self.pipe = pipeline(
            "summarization",
            model=settings.SUMMARIZER_MODEL,
            device=self.device,
            dtype=torch.float16 if self.device == 0 else torch.float32,
        )
        self.pipe.tokenizer.model_max_length = 1024
        self.tokenizer = self.pipe.tokenizer
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len
        )

    def _chunk_text(
        self, 
        text: str, 
        chunk_size: Optional[int] = None, 
        chunk_overlap: Optional[int] = None
    ) -> List[str]:
        """
        Splits text into chunks based on specified chunk size and overlap.
        
        Args:
            text (str): The text to be chunked.
            chunk_size (int): The size of each chunk.
            chunk_overlap (int): The overlap between chunks.

        Returns:
            List[str]: A list of text chunks.
        """
        c_size = chunk_size if chunk_size is not None else settings.CHUNK_SIZE
        c_overlap = chunk_overlap if chunk_overlap is not None else settings.CHUNK_OVERLAP

        if c_size != settings.CHUNK_SIZE or c_overlap != settings.CHUNK_OVERLAP:
            temp_splitter = RecursiveCharacterTextSplitter(
                chunk_size=c_size,
                chunk_overlap=c_overlap,
                length_function=len
            )
            return temp_splitter.split_text(text)

        return self.splitter.split_text(text)

    def _gen_kwargs(
        self, 
        input_text: str, 
        base_max: int = settings.BASE_MAX, 
        base_min: int = settings.BASE_MIN
    ) -> Dict[str, int]:
        token_ids = self.tokenizer(input_text, truncation=False)["input_ids"]
        token_length = len(token_ids)

        desired_max = max(base_min, token_length // 2)
        model_max_length = self.tokenizer.model_max_length

        max_len = min(base_max, desired_max, model_max_length, token_length)
        min_len = min(base_min, max_len)

        if token_length < base_min:
            min_len = token_length
            max_len = token_length

        return {"max_length": max_len, "min_length": min_len}
    
    def summarize_texts(
        self,
        texts: List[str],
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> List[str]:
        summaries = []
        for raw in texts:
            chunks = self._chunk_text(
                raw,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )

            for chunk in chunks:
                if not chunk.strip():
                    continue
                kwargs = self._gen_kwargs(chunk)
                # print(kwargs)
                with torch.no_grad():
                    out = self.pipe(
                        chunk,
                        **kwargs,
                        do_sample=False,    # Deterministic for consistency
                        truncation=True,
                        num_beams=2,       # Add beam search for better quality
                        early_stopping=True  # Stop when summary is complete
                    )
                summaries.append(out[0]["summary_text"])
        return summaries