from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Annotated, List
from langchain_core.messages import HumanMessage, AIMessage
import operator

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