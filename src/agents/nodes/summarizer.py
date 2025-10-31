from src.ingest.tools.summarizer import Summarizer
from langchain.messages import AIMessage

summarizer = Summarizer()

def summarize(state):
    """
    Summarize the retrieved text chunks.

    Args:
        state (dict): The current state containing retrieved chunks.
    Returns:
        dict: A dictionary with summaries and messages.
    """
    chunks = state["retrieved_chunks"]
    texts = [c.page_content for c in chunks if c.metadata.get("type") == "text"]
    summaries = summarizer.summarize_texts(texts)
    return {
        "summaries": summaries,
        "messages": [AIMessage(content=f"Summarized {len(summaries)} sections.")]
    }