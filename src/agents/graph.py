from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Annotated, List
import operator

from src.agents.nodes.retriever import retrieve
from src.agents.nodes.summarizer import summarize
from src.agents.nodes.visual_analyzer import analyze_figures
from src.agents.nodes.synthesizer import synthesize
from src.agents.nodes.fact_checker import fact_check

from src.stores.feedback_store import init_feedback

class AgentState(TypedDict):
   messages: Annotated[List, operator.add]
   query: str
   retrieved_chunks: List
   summaries: List[str]
   figure_insights: List[str]
   synthesis: str
   verified: bool
   feedback: str

# Initialize the state graph for the agent
graph = StateGraph(AgentState)
memory = MemorySaver()

init_feedback()

# Conditional edge for feedback
def route_feedback(state):
    if not state.get("verified", True):
        return "feedback"
    return END

# Add nodes
graph.add_node("retrieve", retrieve)
graph.add_node("summarize", summarize)
graph.add_node("analyze_figures", analyze_figures)
graph.add_node("synthesize", synthesize)
graph.add_node("fact_check", fact_check)

# Edges
graph.add_edge(START, "retrieve")
graph.add_edge("retrieve", "summarize")
graph.add_edge("retrieve", "analyze_figures")
graph.add_edge("summarize", "synthesize")
graph.add_edge("analyze_figures", "synthesize")
graph.add_edge("synthesize", "fact_check")
graph.add_edge("fact_check", END)

# graph.set_entry_point("retrieve")

# graph.add_conditional_edges("fact_check", route_feedback, {"feedback": "feedback", END: END})

# Compile
app = graph.compile(checkpointer=memory)