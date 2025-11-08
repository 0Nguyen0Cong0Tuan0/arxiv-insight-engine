from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

analysis_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a research assistant providing deep analysis of academic content.
        Provide detailed analysis that:
        - Examines figures, tables, or specific sections in depth
        - Explains technical concepts clearly
        - Connects findings to broader context
        - Highlights key insights and implications"""),
    ("human", """Analysis request: {query}
        Content to analyze:
        {context}
        Figures and visual content:
        {figures}
        Provide detailed analysis:""")
])

analysis_chain = analysis_prompt | llm

def analyze(state):
    """
    Provide detailed analysis of content, figures, or specific aspects.
    """
    query = state["query"]
    docs = state.get("retrieved_chunks", [])
    figures = state.get("figure_insights", [])
    
    context = "\n\n".join([
        f"[Paper {doc.metadata.get('paper_id', 'Unknown')}]: {doc.page_content}"
        for doc in docs[:8]
    ])
    
    figures_text = "\n\n".join(figures[:3]) if figures else "No figure analysis available."
    
    response = analysis_chain.invoke({
        "query": query,
        "context": context,
        "figures": figures_text
    }).content
    
    return {
        "synthesis": response,
        "messages": [AIMessage(content="Generated detailed analysis.")]
    }