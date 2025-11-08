from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Annotated, List, Literal
import operator

from src.agents.nodes.router import route_query
from src.agents.nodes.retriever import retrieve
from src.agents.nodes.simple_qa import simple_qa
from src.agents.nodes.summarizer import summarize_node
from src.agents.nodes.comparison import compare
from src.agents.nodes.analyzer import analyze
from src.agents.nodes.fact_checker import fact_check_verify
from src.agents.nodes.visual_analyzer import analyze_figures
from src.stores.feedback_store import init_feedback

class AgentState(TypedDict):
    messages: Annotated[List, operator.add]
    query: str
    query_type: str
    route: str
    retrieved_chunks: List
    summaries: List[str]
    figure_insights: List[str]
    synthesis: str
    verified: bool
    feedback: str

# Initialize graph
graph = StateGraph(AgentState)
memory = MemorySaver()
init_feedback()

# Add nodes
graph.add_node("route_query", route_query)
graph.add_node("retrieve", retrieve)
graph.add_node("simple_qa", simple_qa)
graph.add_node("summarize", summarize_node)
graph.add_node("compare", compare)
graph.add_node("analyze", analyze)
graph.add_node("analyze_figures", analyze_figures)
graph.add_node("fact_check", fact_check_verify)

# Define routing logic
def decide_route(state) -> Literal["simple_qa", "summarization", "comparison", "analysis", "fact_check_flow"]:
    """Route based on query type."""
    return state.get("route", "simple_qa")

def needs_figures(state) -> Literal["analyze_figures", "skip_figures"]:
    """Check if query is about figures/visualizations."""
    query_lower = state["query"].lower()
    figure_keywords = ["figure", "graph", "chart", "plot", "visualization", "image", "diagram"]
    
    if any(keyword in query_lower for keyword in figure_keywords):
        return "analyze_figures"
    return "skip_figures"

# Build graph edges
graph.add_edge(START, "route_query")
graph.add_edge("route_query", "retrieve")

# Conditional routing after retrieval
graph.add_conditional_edges(
    "retrieve",
    decide_route,
    {
        "simple_qa": "simple_qa",
        "summarization": "summarize",
        "comparison": "compare",
        "analysis": "analyze",
        "fact_check_flow": "fact_check"
    }
)

# All paths lead to END
graph.add_edge("simple_qa", END)
graph.add_edge("summarize", END)
graph.add_edge("compare", END)
graph.add_edge("fact_check", END)

# Analysis path may need figure analysis
graph.add_conditional_edges(
    "analyze",
    needs_figures,
    {
        "analyze_figures": "analyze_figures",
        "skip_figures": END
    }
)

graph.add_edge("analyze_figures", END)

# Compile graph
app = graph.compile(checkpointer=memory)
print("Smart routing graph compiled successfully!")