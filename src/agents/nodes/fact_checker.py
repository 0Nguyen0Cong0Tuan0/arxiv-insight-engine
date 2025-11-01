from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini")

prompt = ChatPromptTemplate.from_messages([
    ("system", "Verify if the synthesis is supported by retrieved chunks. Be strict."),
    ("human", "Synthesis: {synthesis}\n\nSources: {sources}\n\nIs it faithful? Yes/No + explanation.")
])

def fact_check(state):
    """
    Fact-check the synthesized insights against retrieved chunks.
    
    Args:
        state (dict): The current state containing synthesis and retrieved chunks.
    Returns:
        dict: A dictionary with fact-check result and messages.
    """
    sources = "\n".join([c.page_content[:500] for c in state["retrieved_chunks"][:5]])
    result = llm.invoke(prompt.format(
        synthesis=state["synthesis"],
        sources=sources
    )).content
    verified = "Yes" in result.split("\n")[0]
    return {
        "verified": verified,
        "messages": [AIMessage(content=f"Fact-check: {'PASS' if verified else 'FAIL'}")]
    }