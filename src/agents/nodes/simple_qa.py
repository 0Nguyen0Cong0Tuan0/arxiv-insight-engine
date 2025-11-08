from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a research assistant helping users understand academic papers.
        Answer the user's question based on the retrieved context from research papers.
        - Be concise and accurate
        - Cite specific papers when relevant (use paper_id from metadata)
        - If the context doesn't contain the answer, say so
        - Use clear, accessible language"""),
    ("human", """Question: {query}
        Context from papers:
        {context}
        Provide a clear, concise answer:""")
])

qa_chain = qa_prompt | llm

def simple_qa(state):
    """
    Answer simple questions using retrieved context.
    """
    query = state["query"]
    docs = state.get("retrieved_chunks", [])
    
    # Prepare context
    context = "\n\n".join([
        f"[Paper {doc.metadata.get('paper_id', 'Unknown')}]: {doc.page_content[:500]}"
        for doc in docs[:5]
    ])
    
    # Generate answer
    response = qa_chain.invoke({
        "query": query,
        "context": context
    }).content
    
    return {
        "synthesis": response,
        "messages": [AIMessage(content="Generated answer using simple QA.")]
    }