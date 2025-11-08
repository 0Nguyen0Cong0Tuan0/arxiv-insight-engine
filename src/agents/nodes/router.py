from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from typing import Literal

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

router_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a routing assistant that analyzes user queries and determines the best processing path.
        Analyze the query and classify it into ONE of these categories:
        1. SIMPLE_QA: Direct questions that need factual answers from documents
        Examples: "What is GPT?", "How does the model work?", "What are the results?"
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

router_chain = router_prompt | llm

def route_query(state) -> dict:
    """
    Determine the query type and set the routing path.
    """
    query = state["query"]
    
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
    
    route = route_mapping.get(result, "simple_qa")  # Default to simple QA
    
    print(f"🔀 Router Decision: {result} → {route}")
    
    return {
        "query_type": result,
        "route": route,
        "messages": []
    }