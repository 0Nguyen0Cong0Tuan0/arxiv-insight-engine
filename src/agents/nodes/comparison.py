from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

comparison_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a research assistant specializing in comparing methods, approaches, and findings across papers.
        Create a structured comparison based on the retrieved context:
        - Identify key dimensions to compare
        - Highlight similarities and differences
        - Provide objective analysis
        - Cite specific papers"""),
    ("human", """Question: {query}
        Context from papers:
        {context}
        Provide a detailed comparison:""")
])

comparison_chain = comparison_prompt | llm

def compare(state):
    """
    Compare concepts, methods, or findings across papers.
    """
    query = state["query"]
    docs = state.get("retrieved_chunks", [])
    
    context = "\n\n".join([
        f"[Paper {doc.metadata.get('paper_id', 'Unknown')}]: {doc.page_content}"
        for doc in docs[:8]
    ])
    
    response = comparison_chain.invoke({
        "query": query,
        "context": context
    }).content
    
    return {
        "synthesis": response,
        "messages": [AIMessage(content="Generated comparison analysis.")]
    }