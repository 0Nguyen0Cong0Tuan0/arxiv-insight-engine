from langchain_core.prompts import ChatPromptTemplate
from typing import Literal
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

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

router_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a routing assistant that analyzes user queries and determines the best processing path.
    Analyze the query and classify it into ONE of these categories:
    1. SIMPLE_QA: Direct questions that need factual answers from documents
    Examples: "What is 3DGS?", "How does the model work?", "What are the results?"
    2. SUMMARIZATION: Requests to summarize or condense information
    Examples: "Summarize the paper", "Give me a brief overview", "What are the key points?"
    3. COMPARISON: Questions comparing different concepts or papers
    Examples: "Compare method A and B", "What's the difference between...", "Which is better?"
    4. ANALYSIS: Deep analysis requests about figures, tables, or detailed explanations
    Examples: "Explain this figure", "Analyze the results table", "What does this visualization show?"
    5. FACT_CHECK: User provides information and wants verification
    Examples: "The process is X. Is this correct?", "I think it works like Y. Can you verify?"
    Respond with ONLY the category name, nothing else."""), ("human", "{query}")
])

router_chain = router_prompt | chat_model

def route_query(state) -> dict:
    """Determine the query type and set the routing path."""
    query = state["query"]
    
    try:
        # Get routing decision
        result = router_chain.invoke({"query": query}).content.strip()
        
        # Map to route
        route_mapping = {
            "SIMPLE_QA": "simple_qa",
            "SUMMARIZATION": "summarization",
            "COMPARISON": "comparison",
            "ANALYSIS": "analysis",
            "FACT_CHECK": "fact_check_flow"
        }
        
        route = route_mapping.get(result, "simple_qa")
        
        print(f"Router Decision: {result} → {route}")
        
        return {
            "query_type": result,
            "route": route,
            "messages": []
        }
    except Exception as e:
        print(f"Router error: {e}, defaulting to simple_qa")
        return {
            "query_type": "SIMPLE_QA",
            "route": "simple_qa",
            "messages": []
        }
