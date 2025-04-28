import streamlit as st
import requests as rq
from pydantic import BaseModel

class ApiInput(BaseModel):
    prompt: str

def get_chat(prompt: str):
    response = rq.post("http://backend:8000/chat/", json=ApiInput(prompt=prompt).model_dump())
    actual_res = response.json()["response"]
    actual_proc = response.json()["process"]
    return actual_res, actual_proc

st.title("Code RAGent💻")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        stream, proc = get_chat(
            prompt=st.session_state.messages[-1]["content"],
        )
        response = st.write(stream)
        st.session_state.messages.append({"role": "assistant", "content": stream})
        with st.expander("See Agentic Process"):
            st.write(proc)