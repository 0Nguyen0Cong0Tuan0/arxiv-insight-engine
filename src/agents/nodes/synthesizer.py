from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from src.monitoring.metrics_tracker import track_node_execution

from config import settings

# Initialize a HuggingFaceEndpoint LLM
llm = HuggingFaceEndpoint(
    repo_id=settings.LLM_MODEL,
    task=settings.LLM_TASK,
    max_new_tokens=settings.LLM_MAX_NEW_TOKENS,
    do_sample=False,
)

# Create a ChatHuggingFace instance with the LLM
chat_model = ChatHuggingFace(llm=llm)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a senior AI researcher. Synthesize insights across papers using Tree-of-Thoughts."),
    ("human", 
        """
        Query: {query}

        Paper Summaries:
        {summaries}

        Figure Insights:
        {figures}

        Generate a comprehensive, cited answer.
        """
    )
])

@track_node_execution("synthesize")
def synthesize(state):
    """
    Synthesize insights across multiple papers.

    Args:
        state (dict): The current state containing summaries and figure insights.
    Returns:
        dict: A dictionary with synthesized insights and messages.
    """
    input_data = {
        "query": state["query"],
        "summaries": "\n".join(state.get("summaries", [])[:3]),
        "figures": "\n".join(state.get("figure_insights", [])[:2])
    }
    response = chat_model.invoke(prompt.format(**input_data)).content
    return {
        "synthesis": response,
        "messages": [AIMessage(content="Synthesized cross-paper insights.")]
    }