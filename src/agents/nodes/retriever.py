from src.agents.tools.hybrid_retriever import get_hybrid_retriever
from langchain.messages import AIMessage

retriever = get_hybrid_retriever()

def retrieve(state):
    """
    Retrieve relevant documents based on the user's query.

    Args:
        state (dict): The current state containing the user's query.
    Returns:
        dict: A dictionary containing the retrieved chunks and a message.
    """
    query = state["query"]
    docs = retriever.invoke(query)
    return {
        "retrieved_chunks": docs,
        "messages": [AIMessage(content=f"Retrieved {len(docs)} chunks.")]
    }