from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

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
    response = llm.invoke(prompt.format(**input_data)).content
    return {
        "synthesis": response,
        "messages": [AIMessage(content="Synthesized cross-paper insights.")]
    }