from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from src.agents.tools.image_captioner import ImageCaptioner

from config import settings

captioner = ImageCaptioner()

# Initialize a HuggingFaceEndpoint LLM
llm = HuggingFaceEndpoint(
    repo_id=settings.LLM_MODEL,
    task=settings.LLM_TASK,
    max_new_tokens=settings.LLM_MAX_NEW_TOKENS,
    do_sample=False,
)

# Create a ChatHuggingFace instance with the LLM
chat_model = ChatHuggingFace(llm=llm)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a visual research assistant. Explain this figure in the context of research."),
    ("human", "Figure caption: {caption}\nImage description: {desc}\nExplain its significance.")
])

chain = prompt | chat_model

def analyze_figures(state):
    """Analyze and explain figures from the retrieved chunks."""
    chunks = state.get("retrieved_chunks", [])
    insights = []
    
    for c in chunks:
        if c.metadata.get("type") == "figure" and c.metadata.get("caption"):
            try:
                insight = chain.invoke({
                    "caption": c.metadata.get("caption", ""),
                    "desc": c.page_content
                }).content
                insights.append(insight)
            except Exception as e:
                print(f"Figure analysis error: {e}")
                continue
    
    return {
        "figure_insights": insights,
        "messages": [AIMessage(content=f"Analyzed {len(insights)} figures.")]
    }