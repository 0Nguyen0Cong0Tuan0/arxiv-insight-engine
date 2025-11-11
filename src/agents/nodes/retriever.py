from src.agents.tools.hybrid_retriever import EnsembleRetriever
from langchain_core.messages import AIMessage
from src.monitoring.metrics_tracker import track_node_execution


# Initialize with a proper corpus fetch
retriever = EnsembleRetriever([]).get_hybrid_retriever()

@track_node_execution("retrieve")
def retrieve(state):
    """
    Retrieve relevant documents based on the user's query.
    """
    query = state["query"]
    docs = retriever.retrieve(query)
    return {
        "retrieved_chunks": docs, 
        "messages": [AIMessage(content=f"Retrieved {len(docs)} chunks.")]
    }