from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
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

comparison_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a research assistant specializing in comparing methods, approaches, and findings across papers.
    Create a structured comparison based on the retrieved context:
    - Identify key dimensions to compare
    - Highlight similarities and differences
    - Provide objective analysis
    - Cite specific papers"""),
    ("human", """Question: {query}
    Context from papers: {context}
    Provide a detailed comparison:""")
])

comparison_chain = comparison_prompt | chat_model

def compare(state):
    """Compare concepts, methods, or findings across papers."""
    query = state["query"]
    docs = state.get("retrieved_chunks", [])
    
    context = "\n\n".join([
        f"[Paper {doc.metadata.get('paper_id', 'Unknown')}]: {doc.page_content}"
        for doc in docs[:8]
    ])
    
    try:
        response = comparison_chain.invoke({
            "query": query,
            "context": context
        }).content
        
        return {
            "synthesis": response,
            "messages": [AIMessage(content="Generated comparison analysis.")]
        }
    except Exception as e:
        print(f"Comparison error: {e}")
        return {
            "synthesis": f"Error generating comparison: {str(e)}",
            "messages": [AIMessage(content=f"Error: {e}")]
        }