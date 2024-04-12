import streamlit as st
from langchain_community.llms import Ollama
from langchain.agents import AgentType, initialize_agent, load_tools, create_react_agent, AgentExecutor
from langchain.callbacks.manager import CallbackManager
from langchain_community.callbacks import StreamlitCallbackHandler
from langchain.callbacks.streaming_stdout_final_only import FinalStreamingStdOutCallbackHandler
from nltk.tokenize import word_tokenize
from langchain_core.prompts import PromptTemplate
import nltk


template = '''Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!
Context:{context}
Question: {input}
Thought:{agent_scratchpad}
'''

prompt_template = PromptTemplate.from_template(template)

nltk.download('punkt', quiet=True)

st.title("JYLA (Just Your Lazy AI)")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Add delete button to the sidebar
if st.sidebar.button("Delete All Messages"):
    # Clear the messages stored in session state
    st.session_state.messages = []
    # Reload the page to reflect changes
    #st.experimental_rerun()

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
prompt = st.chat_input("What's on your mind?")
# Checkbox for internet search option
search_internet = st.sidebar.checkbox("Check internet?", value=False, key="internet")
if prompt:
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})

    tokens = sum(len(word_tokenize(m["content"])) for m in st.session_state.messages)
    while tokens > 7500:  # Adjust as per model's token limit
        st.session_state.messages.pop(0)
        tokens = sum(len(word_tokenize(m["content"])) for m in st.session_state.messages)

    context = "\n".join(m["content"] for m in st.session_state.messages if m["role"] == "user")

    if not search_internet:
        with st.spinner("Searching for the answer to: "+prompt):
            try:
                llm = Ollama(model="mistral:instruct")
                response = llm.invoke("Context: "+context+" Current Question: "+prompt)
                st.session_state.messages.append({"role": "assistant", "content": response})
                with st.chat_message("assistant"):
                    st.write(response)
            except:
                st.markdown("Could not process request.  Please Try Again")
    else:
        with st.spinner("Using the web to find the answer to: "+prompt):
            try:
                llm = Ollama(
                    model="mistral:instruct", 
                    callback_manager=CallbackManager([FinalStreamingStdOutCallbackHandler()])
                )
                tools = load_tools(["ddg-search"])
                agent = create_react_agent(llm, tools, prompt_template)
                agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True,  handle_parsing_errors=True, callbacks=[StreamlitCallbackHandler(st.container())])  
                response = agent_executor.invoke({"input": prompt, "context":context})
                st.session_state.messages.append({"role": "assistant", "content": response['output']})
                with st.chat_message("assistant"):
                    st.markdown(response['output'])
            except:
                st.markdown("Could not process request.  Please Try Again")
