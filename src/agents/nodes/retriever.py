from src.agents.tools.hybrid_retriever import EnsembleRetriever
from langchain_core.messages import AIMessage

# Initialize with a proper corpus fetch
retriever = EnsembleRetriever([]).get_hybrid_retriever()

def retrieve(state):
    """
    Retrieve relevant documents based on the user's query.

    Args:
        state (dict): The current state containing the user's query.
    Returns:
        dict: A dictionary containing the retrieved chunks and a message.
    """
    query = state["query"]
    docs = retriever.retrieve(query)  # Use retrieve method
    return {
        "retrieved_chunks": docs,  # Fixed key to match state
        "messages": [AIMessage(content=f"Retrieved {len(docs)} chunks.")]
    }