from src.agents.tools.summarizer import Summarizer
from langchain_core.messages import AIMessage

summarizer = Summarizer()

def summarize_node(state):
    """
    Summarize the retrieved text chunks or generate a summary answer.
    """
    chunks = state.get("retrieved_chunks", [])
    
    if not chunks:
        return {
            "synthesis": "No documents found to summarize.",
            "summaries": [],
            "messages": [AIMessage(content="No documents to summarize.")]
        }
    
    # Extract text content
    texts = [c.page_content for c in chunks if c.page_content]
    
    # Summarize
    summaries = summarizer.summarize_texts(texts[:5])  # Limit to top 5
    
    # Combine summaries
    combined = "\n\n".join(summaries)
    
    return {
        "summaries": summaries,
        "synthesis": f"Summary of retrieved papers:\n\n{combined}",
        "messages": [AIMessage(content=f"Summarized {len(summaries)} sections.")]
    }