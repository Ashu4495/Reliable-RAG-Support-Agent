import streamlit as st
import json
from app.agent import SupportAgent

# Set page config
st.set_page_config(
    page_title="Aster & Row Support Agent",
    page_icon="🎒",
    layout="wide",
)

st.title("🎒 Aster & Row Customer Support Agent")
st.caption("Reliable, grounded AI assistant for bags, drinkware, and travel accessories.")

# Initialize agent in session state
if "agent" not in st.session_state:
    st.session_state.agent = SupportAgent()
    st.session_state.session_id = "streamlit_session_1"
    st.session_state.messages = []

# Sidebar Controls
with st.sidebar:
    st.header("⚙️ Configuration & Diagnostics")
    provider_name = st.session_state.agent.provider.upper()
    st.info(f"**Active Engine:** `{provider_name}`")
    
    debug_mode = st.toggle("🐞 Debug / Log Mode", value=False)
    
    if st.button("🔄 Clear Conversation", use_container_width=True):
        st.session_state.agent.session_manager.clear_session(st.session_state.session_id)
        st.session_state.messages = []
        st.rerun()
        
    st.markdown("---")
    st.markdown("### 💡 Quick Sample Prompts")
    quick_prompts = [
        "How long do I have to return an unused backpack?",
        "Where is ORD-1007 and when will it arrive?",
        "Do you ship to Canada?",
        "Can I wash the Breeze Tumbler in the dishwasher?",
        "Are all fabrics and adhesives in your bags vegan?",
    ]
    for qp in quick_prompts:
        if st.button(qp, key=f"btn_{qp}", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": qp})
            result = st.session_state.agent.process_message(qp, session_id=st.session_state.session_id)
            st.session_state.messages.append({
                "role": "assistant",
                "content": result["response"],
                "sources": result["sources"],
                "citations": result["citations"],
                "tool_called": result["tool_called"],
                "needs_handoff": result["needs_handoff"],
                "debug_trace": result["debug_trace"],
            })
            st.rerun()

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        
        if msg["role"] == "assistant":
            # Show human handoff banner if flagged
            if msg.get("needs_handoff"):
                st.warning("⚠️ **Human Support Recommended:** This request involves an exception, active policy conflict, or requires human review.")
            
            # Show Citations
            citations = msg.get("citations", [])
            if citations:
                with st.expander("📚 Sources & Citations"):
                    for c in citations:
                        st.markdown(f"- `{c}`")

            # Show Debug Details
            if debug_mode and "debug_trace" in msg:
                with st.expander("🔍 Observability & Debug Trace", expanded=False):
                    st.json(msg["debug_trace"])

# User Input
if prompt := st.chat_input("Ask a question about policies, products, or order status..."):
    # Render user prompt
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Process via agent
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            result = st.session_state.agent.process_message(prompt, session_id=st.session_state.session_id)
            st.write(result["response"])
            
            if result["needs_handoff"]:
                st.warning("⚠️ **Human Support Recommended:** This request involves an exception, active policy conflict, or requires human review.")
            
            if result["citations"]:
                with st.expander("📚 Sources & Citations"):
                    for c in result["citations"]:
                        st.markdown(f"- `{c}`")
                        
            if debug_mode:
                with st.expander("🔍 Observability & Debug Trace", expanded=False):
                    st.json(result["debug_trace"])

    st.session_state.messages.append({
        "role": "assistant",
        "content": result["response"],
        "sources": result["sources"],
        "citations": result["citations"],
        "tool_called": result["tool_called"],
        "needs_handoff": result["needs_handoff"],
        "debug_trace": result["debug_trace"],
    })
