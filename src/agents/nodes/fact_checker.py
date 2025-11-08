from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

fact_check_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a fact-checking assistant. Verify claims against research papers.
        Your task:
        1. Extract the claim from the user's query
        2. Check if it's supported by the retrieved papers
        3. Provide evidence or corrections
        4. Be precise and cite sources"""),
    ("human", """User's claim/question: {query}
        Evidence from papers:
        {context}
        Verify the claim and provide a detailed response:""")
])

fact_check_chain = fact_check_prompt | llm

def fact_check_verify(state):
    """
    Verify user's claims or statements against retrieved papers.
    """
    query = state["query"]
    docs = state.get("retrieved_chunks", [])
    
    context = "\n\n".join([
        f"[Paper {doc.metadata.get('paper_id', 'Unknown')}]: {doc.page_content[:500]}"
        for doc in docs[:5]
    ])
    
    response = fact_check_chain.invoke({
        "query": query,
        "context": context
    }).content
    
    return {
        "synthesis": response,
        "verified": True,
        "messages": [AIMessage(content="Fact-checked claim against papers.")]
    }