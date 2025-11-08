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

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a research assistant helping users understand academic papers.
    Answer the user's question based on the retrieved context from research papers.
    - Be concise and accurate
    - Cite specific papers when relevant (use paper_id from metadata)
    - If the context doesn't contain the answer, say so
    - Use clear, accessible language"""),
    ("human", """Question: {query}
    Context from papers: {context}
    Provide a clear, concise answer:""")
])

qa_chain = qa_prompt | chat_model

def simple_qa(state):
    """Answer simple questions using retrieved context."""
    query = state["query"]
    docs = state.get("retrieved_chunks", [])
    
    if not docs:
        return {
            "synthesis": "I couldn't find any relevant information in the documents. Please make sure papers are uploaded and indexed.",
            "messages": [AIMessage(content="No documents found.")]
        }
    
    # Prepare context
    context = "\n\n".join([
        f"[Paper {doc.metadata.get('paper_id', 'Unknown')}]: {doc.page_content[:500]}"
        for doc in docs[:5]
    ])
    
    try:
        # Generate answer
        response = qa_chain.invoke({
            "query": query,
            "context": context
        }).content
        
        return {
            "synthesis": response,
            "messages": [AIMessage(content="Generated answer using simple QA.")]
        }
    except Exception as e:
        print(f"QA error: {e}")
        return {
            "synthesis": f"Error generating answer: {str(e)}",
            "messages": [AIMessage(content=f"Error: {e}")]
        }