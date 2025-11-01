import streamlit as st
from src.agents.graph import app
from stores.feedback_store import store_feedback
from langgraph.prebuilt import ToolNode
import uuid

st.title("ArXiv Insight Engine")

query = st.text_input("Ask a research question:")
if st.button("Run"):
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    result = app.invoke({"query": query, "messages": []}, config)
    
    st.write("### Final Answer")
    st.write(result["synthesis"])
    
    if not result.get("verified"):
        feedback = st.text_area("Correct the answer:")
        if st.button("Submit Feedback"):
            store_feedback(query, feedback)
            st.success("Feedback saved! System will improve.")
    
    with st.expander("Agent Trace"):
        for msg in result["messages"]:
            st.write(f"**{msg.type}**: {msg.content}")