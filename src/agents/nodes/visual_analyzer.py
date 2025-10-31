from src.ingest.tools.image_captioner import ImageCaptioner
from langchain.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

captioner = ImageCaptioner()
llm = ChatOpenAI(model="gpt-4o-mini")

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a visual research assistant. Explain this figure in the context of LLM research."),
    ("human", "Figure caption: {caption}\nImage description: {desc}\nExplain its significance.")
])

chain = prompt | llm

def analyze_figures(state):
    """
    Analyze and explain figures from the retrieved chunks.

    Args:
        state (dict): The current state containing retrieved chunks.
    Returns:
        dict: A dictionary with figure insights and messages.
    """
    chunks = state["retrieved_chunks"]
    insights = []
    for c in chunks:
        if c.metadata.get("type") == "figure" and c.metadata.get("caption"):
            insight = chain.invoke({
                "caption": c.metadata.get("caption", ""),
                "desc": c.page_content
            }).content
            insights.append(insight)
    return {
        "figure_insights": insights,
        "messages": [AIMessage(content=f"Analyzed {len(insights)} figures.")]
    }