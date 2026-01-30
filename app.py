import streamlit as st
import asyncio
import os
from langchain_core.messages import HumanMessage, AIMessage
from agent import get_agent
from ingestion_utils import ingest_folder

st.set_page_config(
    page_title="Endee Codebase Agent",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Endee Codebase Agent")
st.markdown("Ask questions about your codebase, structure, or implementation details.")

with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.subheader("Ingest Codebase")
    default_path = os.getcwd()
    codebase_name = st.text_input("Codebase Name", value="default_codebase")
    path_input = st.text_input("Codebase Path", value=default_path)
    
    if st.button("Ingest Codebase"):
        if path_input and os.path.exists(path_input) and codebase_name:
            with st.spinner(f"Ingesting {path_input} into '{codebase_name}'..."):
                try:
                    ingest_folder(path_input, codebase_name)
                    st.success("Ingestion complete!")
                    st.cache_resource.clear()
                except Exception as e:
                    st.error(f"Ingestion failed: {e}")
        else:
            st.error("Please enter a valid path and codebase name.")

    st.markdown("---")
    st.header("Status")
    
    st.markdown("**Instructions:**")
    st.markdown("- Ask specific questions about files.")
    st.markdown("- Ask 'How does X work?'.")
    st.markdown("- Ask 'Show me the class Y'.")


# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

@st.cache_resource
def load_agent_resource(name: str):
    return get_agent(name)

try:
    if codebase_name:
        agent = load_agent_resource(codebase_name)
    else:
        st.warning("Please enter a codebase name to load the agent.")
        agent = None
        
except Exception as e:
    st.error(f"Failed to load agent: {e}")
    st.stop()

if agent:
     with st.sidebar:
          st.success("Agent Active")

for message in st.session_state.messages:
    if isinstance(message, HumanMessage):
        role = "user"
        content = message.content
    else:
        role = "assistant"
        content = message.content
        
    with st.chat_message(role):
        st.markdown(content)

if prompt := st.chat_input("Ask about the codebase..."):
    # Add user message to state
    st.session_state.messages.append(HumanMessage(content=prompt))
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        
        try:
            # Run the agent
            inputs = {"messages": st.session_state.messages}
            response = agent.invoke(inputs)
            last_message = response["messages"][-1]
            full_response = last_message.content
            message_placeholder.markdown(full_response)
            st.session_state.messages.append(AIMessage(content=full_response))
            
        except Exception as e:
            message_placeholder.markdown(f"Error: {e}")
            st.error(f"An error occurred: {e}")