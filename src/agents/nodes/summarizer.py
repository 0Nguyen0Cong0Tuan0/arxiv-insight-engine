from src.agents.tools.summarizer import Summarizer
from langchain_core.messages import AIMessage

summarizer = Summarizer()

def summarize(state):
    """
    Summarize the retrieved text chunks.

    Args:
        state (dict): The current state containing retrieved chunks.
    Returns:
        dict: A dictionary with summaries and messages.
    """
    print(state)
    chunks = state["retrieved_chunks"]["docs"]
    print(chunks)
    texts = [c.page_content for c in chunks]
    summaries = summarizer.summarize_texts(texts)
    return {
        "summaries": summaries,
        "messages": [AIMessage(content=f"Summarized {len(summaries)} sections.")]
    }